"""Package installation functionality"""

import sys
import json
import shutil
import traceback
import zipfile
import tempfile
from pathlib import Path
from urllib import request
from urllib.error import URLError, HTTPError

from .utils import get_mip_packages_dir
from .matlab_integration import _ensure_mip_matlab_setup
from .dependency_graph import _build_dependency_graph, _topological_sort_packages
from .platform_utils import (
    get_current_architecture_tag,
    select_best_package_variant,
    get_available_architectures_for_package
)

def _download_and_install(package_name, package_info, mip_dir):
    """Download and install a single package
    
    Args:
        package_name: Name of the package
        package_info: Package info from index
        mip_dir: The mip directory path
    """
    package_dir = mip_dir / package_name
    
    # Get filename
    mhl_url = package_info['mhl_url']
    
    print(f"Downloading {package_name} {package_info['version']}...")
    
    # Create temporary file for download
    mhl_path = mip_dir / f"{package_name}.mhl"
    request.urlretrieve(mhl_url, mhl_path)
    
    # Extract the .mhl file (which is a zip file)
    print(f"Extracting {package_name}...")
    with zipfile.ZipFile(mhl_path, 'r') as zip_ref:
        zip_ref.extractall(package_dir)
    
    # Clean up .mhl file
    mhl_path.unlink()
    
    print(f"Successfully installed '{package_name}'")

def _install_from_mhl(mhl_source, mip_dir):
    """Install a package from a local .mhl file or URL
    
    Args:
        mhl_source: Path to local .mhl file or URL to .mhl file
        mip_dir: The mip directory path
    """
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_extract_dir = Path(temp_dir) / "extracted"
        temp_extract_dir.mkdir()
        
        # Download or copy the .mhl file
        if mhl_source.startswith('http://') or mhl_source.startswith('https://'):
            print(f"Downloading {mhl_source}...")
            mhl_path = Path(temp_dir) / "package.mhl"
            try:
                request.urlretrieve(mhl_source, mhl_path)
            except (HTTPError, URLError) as e:
                print(f"Error: Could not download .mhl file: {e}")
                sys.exit(1)
        else:
            # Local file
            mhl_path = Path(mhl_source)
            if not mhl_path.exists():
                print(f"Error: File not found: {mhl_source}")
                sys.exit(1)
            if not mhl_path.is_file():
                print(f"Error: Not a file: {mhl_source}")
                sys.exit(1)
        
        # Extract the .mhl file
        print(f"Extracting package...")
        try:
            with zipfile.ZipFile(mhl_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
        except zipfile.BadZipFile:
            print(f"Error: Invalid .mhl file (not a valid zip file)")
            sys.exit(1)
        
        # Read mip.json to get package name and dependencies
        mip_json_path = temp_extract_dir / 'mip.json'
        if not mip_json_path.exists():
            print(f"Error: Package is missing mip.json file")
            sys.exit(1)
        
        try:
            with open(mip_json_path, 'r') as f:
                mip_config = json.load(f)
        except Exception as e:
            print(f"Error: Could not read mip.json: {e}")
            sys.exit(1)
        
        # Get package name
        package_name = mip_config.get('name')
        if not package_name:
            print(f"Error: Package name not found in mip.json")
            print(f"The mip.json file must contain a 'name' field with the package name")
            sys.exit(1)
        
        # Check if package is already installed
        package_dir = mip_dir / package_name
        if package_dir.exists():
            print(f"Package '{package_name}' is already installed")
            return
        
        # Get dependencies
        dependencies = mip_config.get('dependencies', [])
        
        # Install dependencies from remote repository
        if dependencies:
            print(f"\nPackage '{package_name}' has dependencies: {', '.join(dependencies)}")
            print(f"Installing dependencies from remote repository...")
            for dep in dependencies:
                # Check if dependency is already installed
                dep_dir = mip_dir / dep
                if dep_dir.exists():
                    print(f"Dependency '{dep}' is already installed")
                else:
                    print(f"\nInstalling dependency '{dep}'...")
                    install_package(dep)
        
        # Install the package
        print(f"\nInstalling '{package_name}'...")
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all files from temp extraction directory to package directory
        for item in temp_extract_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, package_dir)
            elif item.is_dir():
                shutil.copytree(item, package_dir / item.name)
        
        print(f"Successfully installed '{package_name}'")

def install_package(package_names):
    """Install one or more packages from the mip repository, local .mhl files, or URLs
    
    Args:
        package_names: Package name(s) to install. Can be:
                      - A single string (package name, .mhl file path, or URL)
                      - A list of strings (multiple packages)
    """
    # Ensure MATLAB integration is up to date
    _ensure_mip_matlab_setup()
    
    mip_dir = get_mip_packages_dir()
    mip_dir.mkdir(parents=True, exist_ok=True)
    
    # Normalize input to a list
    if isinstance(package_names, str):
        package_names = [package_names]
    
    # Separate packages by type
    repo_packages = []
    mhl_sources = []
    
    for pkg in package_names:
        if pkg.endswith('.mhl'):
            mhl_sources.append(pkg)
        else:
            repo_packages.append(pkg)
    
    # Phase 1: Validate and plan installations
    all_packages_to_install = []
    package_info_map = {}
    
    # Handle repository packages
    if repo_packages:
        try:
            # Download and parse the package index once
            index_url = "https://mip-org.github.io/mip-core/index.json"
            print(f"Fetching package index...")
            
            with request.urlopen(index_url) as response:
                index_content = response.read().decode('utf-8')
            
            index = json.loads(index_content)
            
            # Get current architecture and filter packages by compatibility
            current_architecture = get_current_architecture_tag()
            print(f"Detected architecture: {current_architecture}")

            # Group packages by name to handle multiple architecture variants
            packages_by_name = {}
            for pkg in index.get('packages', []):
                name = pkg['name']
                if name not in packages_by_name:
                    packages_by_name[name] = []
                packages_by_name[name].append(pkg)
            
            # Select best variant for each package
            package_info_map = {}
            unavailable_packages = {}
            
            for name, variants in packages_by_name.items():
                best_variant = select_best_package_variant(variants, current_architecture)
                if best_variant:
                    package_info_map[name] = best_variant
                else:
                    # Track packages with no compatible variant
                    unavailable_packages[name] = get_available_architectures_for_package(variants)
            
            # Check if any requested packages are unavailable for this architecture
            for pkg_name in repo_packages:
                if pkg_name not in package_info_map:
                    if pkg_name in unavailable_packages:
                        available_architectures = unavailable_packages[pkg_name]
                        print(f"\nError: Package '{pkg_name}' is not available for architecture '{current_architecture}'")
                        print(f"Available architectures: {', '.join(available_architectures)}")
                        sys.exit(1)
                    else:
                        # Package doesn't exist at all
                        print(f"Error: Package '{pkg_name}' not found in repository")
                        sys.exit(1)
            
            # Resolve dependencies for all requested packages
            if len(repo_packages) == 1:
                print(f"Resolving dependencies for '{repo_packages[0]}'...")
            else:
                print(f"Resolving dependencies for {len(repo_packages)} packages...")
            
            # Build combined dependency graph using the filtered package_info_map
            all_required = set()
            for pkg_name in repo_packages:
                install_order = _build_dependency_graph(pkg_name, package_info_map)
                all_required.update(install_order)
            
            # Convert to list and sort topologically
            # We need to rebuild the order considering all packages together
            all_packages_to_install = _topological_sort_packages(list(all_required), package_info_map)
            
        except HTTPError as e:
            traceback.print_exc()
            print(f"Error: Could not download package index (HTTP {e.code})")
            sys.exit(1)
        except URLError as e:
            traceback.print_exc()
            print(f"Error: Could not connect to package repository: {e.reason}")
            sys.exit(1)
        except Exception as e:
            traceback.print_exc()
            print(f"Error: Failed to resolve dependencies: {e}")
            sys.exit(1)
    
    # Handle .mhl file installations
    # For .mhl files, we'll install them after repo packages
    # since they might depend on repo packages
    for mhl_source in mhl_sources:
        # Note: .mhl installations will handle their own dependencies
        # by calling install_package recursively if needed
        pass
    
    # Filter out already installed packages (repo packages only)
    to_install = []
    already_installed = []
    
    for pkg_name in all_packages_to_install:
        package_dir = mip_dir / pkg_name
        if package_dir.exists():
            already_installed.append(pkg_name)
        else:
            to_install.append(pkg_name)
    
    # Report already installed packages
    if already_installed:
        for pkg_name in already_installed:
            print(f"Package '{pkg_name}' is already installed")
    
    # Show installation plan
    if to_install:
        if len(to_install) == 1:
            print(f"\nInstallation plan:")
        else:
            print(f"\nInstallation plan ({len(to_install)} packages):")
        
        for pkg_name in to_install:
            pkg_info = package_info_map[pkg_name]
            # Show which requested packages require this one
            required_by = []
            for requested in repo_packages:
                if requested != pkg_name:
                    deps = _build_dependency_graph(requested, package_info_map)
                    if pkg_name in deps:
                        required_by.append(requested)
            
            if pkg_name in repo_packages:
                print(f"  - {pkg_name} {pkg_info['version']}")
            elif required_by:
                print(f"  - {pkg_name} {pkg_info['version']} (required by {', '.join(required_by)})")
            else:
                print(f"  - {pkg_name} {pkg_info['version']}")
        print()
    
    # Phase 2: Execute installations
    installed_count = 0
    
    # Install repository packages
    if to_install:
        for pkg_name in to_install:
            pkg_info = package_info_map[pkg_name]
            _download_and_install(pkg_name, pkg_info, mip_dir)
            installed_count += 1
    
    # Install .mhl files
    for mhl_source in mhl_sources:
        _install_from_mhl(mhl_source, mip_dir)
        installed_count += 1
    
    # Summary
    if installed_count == 0 and not mhl_sources:
        print(f"All packages already installed")
    elif installed_count > 0:
        print(f"\nSuccessfully installed {installed_count} package(s)")
