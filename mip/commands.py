"""Command implementations for mip"""

import os
import shutil
import sys
import subprocess
import zipfile
import json
from pathlib import Path
from urllib import request
from urllib.error import URLError, HTTPError


def get_mip_dir():
    """Get the mip packages directory path"""
    home = Path.home()
    return home / '.mip' / 'packages'

def _ensure_mip_matlab_setup():
    """Ensure the +mip directory is set up in ~/.mip/matlab
    
    This is called automatically by install, uninstall, and setup commands
    to ensure users always have the latest version of mip.import()
    """
    try:
        # Get the source +mip directory
        source_mip = Path(__file__).parent / '+mip'
        if not source_mip.exists():
            print("Warning: +mip directory not found in package")
            return
        # Get the source mip.m file
        source_mip_m = Path(__file__).parent / 'mip.m'
        if not source_mip_m.exists():
            print("Warning: mip.m file not found in package")
            return
        
        # Destination path in ~/.mip/matlab/+mip
        home = Path.home()
        dest_plus_mip = home / '.mip' / 'matlab' / '+mip'
        
        # Create parent directory if it doesn't exist
        dest_plus_mip.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the +mip directory (remove old one if it exists)
        if dest_plus_mip.exists():
            shutil.rmtree(dest_plus_mip)
        
        shutil.copytree(source_mip, dest_plus_mip)

        # Copy the mip.m file
        dest_mip_m = home / '.mip' / 'matlab' / 'mip.m'
        shutil.copy2(source_mip_m, dest_mip_m)
        
    except Exception as e:
        print(f"Warning: Failed to update MATLAB integration: {e}")


def _build_dependency_graph(package_name, index, visited=None, path=None):
    """Recursively build a dependency graph for a package
    
    Args:
        package_name: Name of the package
        index: The parsed package index
        visited: Set of already visited packages (for cycle detection)
        path: Current path (for cycle detection)
    
    Returns:
        List of package names in dependency order (dependencies first)
    """
    if visited is None:
        visited = set()
    if path is None:
        path = []
    
    # Check for circular dependency
    if package_name in path:
        cycle = ' -> '.join(path + [package_name])
        print(f"Error: Circular dependency detected: {cycle}")
        sys.exit(1)
    
    # If already visited, skip
    if package_name in visited:
        return []

    # Find package in index
    package_info = None
    for pkg in index.get('packages', []):
        if pkg.get('name') == package_name:
            package_info = pkg
            break
    
    if not package_info:
        print(f"Error: Package '{package_name}' not found in repository")
        sys.exit(1)
    
    visited.add(package_name)
    path.append(package_name)
    
    # Collect all dependencies first
    result = []
    for dep in package_info.get('dependencies', []):
        result.extend(_build_dependency_graph(dep, index, visited, path[:]))

    # Then add this package
    result.append(package_name)
    
    return result


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
    
    print(f"Downloading {package_name} v{package_info['version']}...")
    
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
    import tempfile
    
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
        package_name = mip_config.get('package')
        if not package_name:
            print(f"Error: Package name not found in mip.json")
            print(f"The mip.json file must contain a 'package' field with the package name")
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

def install_package(package_name):
    """Install a package from the mip repository, local .mhl file, or URL
    
    Args:
        package_name: Name of the package to install, path to local .mhl file, or URL to .mhl file
    """
    # Ensure MATLAB integration is up to date
    _ensure_mip_matlab_setup()
    
    mip_dir = get_mip_dir()
    mip_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if this is a local .mhl file or URL
    if package_name.endswith('.mhl'):
        _install_from_mhl(package_name, mip_dir)
        return
    
    # Otherwise, proceed with remote repository installation

    # Download and parse the package index
    index_url = "https://mip-org.github.io/mip-core/index.json"
    print(f"Fetching package index...")
    
    try:
        # Download index
        with request.urlopen(index_url) as response:
            index_content = response.read().decode('utf-8')

        # Parse JSON
        index = json.loads(index_content)

        # Build dependency graph (returns packages in install order)
        print(f"Resolving dependencies for '{package_name}'...")
        install_order = _build_dependency_graph(package_name, index)
        
        # Filter out already installed packages
        to_install = []
        package_info_map = {pkg['name']: pkg for pkg in index.get('packages', [])}

        for pkg_name in install_order:
            package_dir = mip_dir / pkg_name
            if package_dir.exists():
                print(f"Package '{pkg_name}' is already installed")
            else:
                to_install.append(pkg_name)
        
        if not to_install:
            print(f"All packages already installed")
            return
        
        # Show installation plan
        if len(to_install) > 1:
            print(f"\nInstallation plan:")
            for pkg_name in to_install:
                pkg_info = package_info_map[pkg_name]
                print(f"  - {pkg_name} v{pkg_info['version']}")
            print()
        
        # Install each package in order
        for pkg_name in to_install:
            pkg_info = package_info_map[pkg_name]
            _download_and_install(pkg_name, pkg_info, mip_dir)
        
        print(f"\nSuccessfully installed {len(to_install)} package(s)")
        
    except HTTPError as e:
        print(f"Error: Could not download (HTTP {e.code})")
        sys.exit(1)
    except URLError as e:
        print(f"Error: Could not connect to package repository: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to install package '{package_name}': {e}")
        sys.exit(1)


def _read_package_dependencies(package_dir):
    """Read dependencies from a package's mip.json file
    
    Args:
        package_dir: Path to the package directory
    
    Returns:
        List of dependency package names, or empty list if no dependencies or error
    """
    mip_json_path = package_dir / 'mip.json'
    
    if not mip_json_path.exists():
        return []
    
    try:
        with open(mip_json_path, 'r') as f:
            mip_config = json.load(f)
        
        dependencies = mip_config.get('dependencies', [])
        return dependencies if isinstance(dependencies, list) else []
    except Exception as e:
        print(f"Warning: Could not read mip.json for {package_dir.name}: {e}")
        return []

def _find_reverse_dependencies(package_name, mip_dir, visited=None):
    """Find all packages that depend on the given package (recursively)
    
    Args:
        package_name: Name of the package to find reverse dependencies for
        mip_dir: The mip directory path
        visited: Set of already visited packages (for recursion)
    
    Returns:
        List of package names that depend on the given package (directly or indirectly)
    """
    if visited is None:
        visited = set()
    
    # Avoid infinite recursion
    if package_name in visited:
        return []
    
    visited.add(package_name)
    reverse_deps = []
    
    # Scan all installed packages
    if not mip_dir.exists():
        return []
    
    for pkg_dir in mip_dir.iterdir():
        if not pkg_dir.is_dir():
            continue
        
        pkg_name = pkg_dir.name
        
        # Skip the package itself
        if pkg_name == package_name:
            continue
        
        # Read this package's dependencies
        dependencies = _read_package_dependencies(pkg_dir)
        
        # If this package depends on our target package
        if package_name in dependencies:
            reverse_deps.append(pkg_name)
            # Recursively find packages that depend on this package
            transitive_deps = _find_reverse_dependencies(pkg_name, mip_dir, visited)
            reverse_deps.extend(transitive_deps)
    
    return reverse_deps

def uninstall_package(package_name):
    """Uninstall a package and all packages that depend on it"""
    # Ensure MATLAB integration is up to date
    _ensure_mip_matlab_setup()
    
    mip_dir = get_mip_dir()
    package_dir = mip_dir / package_name
    
    # Check if package is installed
    if not package_dir.exists():
        print(f"Package '{package_name}' is not installed")
        return
    
    # Find all packages that depend on this package
    print(f"Scanning for packages that depend on '{package_name}'...")
    reverse_deps = _find_reverse_dependencies(package_name, mip_dir)
    
    # Build the complete uninstall list
    to_uninstall = []
    
    # Add reverse dependencies first (they need to be uninstalled before their dependencies)
    if reverse_deps:
        # Remove duplicates while preserving order
        seen = set()
        unique_reverse_deps = []
        for dep in reverse_deps:
            if dep not in seen:
                seen.add(dep)
                unique_reverse_deps.append(dep)
        to_uninstall.extend(unique_reverse_deps)
    
    # Add the target package last
    to_uninstall.append(package_name)
    
    # Display uninstallation plan
    if len(to_uninstall) > 1:
        print(f"\nThe following packages will be uninstalled:")
        for pkg in to_uninstall:
            if pkg == package_name:
                print(f"  - {pkg}")
            else:
                print(f"  - {pkg} (depends on {package_name})")
        print()
    
    # Confirm uninstallation
    if len(to_uninstall) == 1:
        response = input(f"Are you sure you want to uninstall '{package_name}'? (y/n): ")
    else:
        response = input(f"Are you sure you want to uninstall these {len(to_uninstall)} packages? (y/n): ")
    
    if response.lower() not in ['y', 'yes']:
        print("Uninstallation cancelled")
        return
    
    # Uninstall all packages
    print()
    for pkg in to_uninstall:
        pkg_dir = mip_dir / pkg
        if pkg_dir.exists():
            try:
                print(f"Uninstalling '{pkg}'...")
                shutil.rmtree(pkg_dir)
                print(f"Successfully uninstalled '{pkg}'")
            except Exception as e:
                print(f"Error: Failed to uninstall package '{pkg}': {e}")
                sys.exit(1)
    
    print(f"\nSuccessfully uninstalled {len(to_uninstall)} package(s)")


def list_packages():
    """List all installed packages with their versions"""
    mip_dir = get_mip_dir()
    
    if not mip_dir.exists():
        print("No packages installed yet")
        return
    
    packages = [d.name for d in mip_dir.iterdir() if d.is_dir()]
    
    if not packages:
        print("No packages installed yet")
    else:
        print("Installed packages:")
        for package in sorted(packages):
            package_dir = mip_dir / package
            mip_json_path = package_dir / 'mip.json'
            
            # Try to read version from mip.json
            version = None
            if mip_json_path.exists():
                try:
                    with open(mip_json_path, 'r') as f:
                        mip_config = json.load(f)
                    version = mip_config.get('version')
                except Exception:
                    pass
            
            # Display package with version if available
            if version:
                print(f"  - {package} (v{version})")
            else:
                print(f"  - {package}")


def setup_matlab():
    """Refresh the +mip directory in ~/.mip/matlab
    
    This ensures you have the latest version of mip.import() after upgrading mip.
    The MATLAB integration is also automatically updated when running install or uninstall commands.
    """
    # Ensure MATLAB integration is up to date
    _ensure_mip_matlab_setup()
    
    home = Path.home()
    mip_matlab_dir = home / '.mip' / 'matlab'
    
    print(f"MATLAB integration updated at: {mip_matlab_dir}")
    print(f"\nMake sure to add '{mip_matlab_dir}' to your MATLAB path.")
    print(f"You can do this by running in MATLAB:")
    print(f"  addpath('{mip_matlab_dir}')")
    print(f"  savepath")

def find_name_collisions():
    """Find and report name collisions in exposed symbols across all installed packages"""
    mip_dir = get_mip_dir()
    
    if not mip_dir.exists():
        print("No packages installed yet")
        return
    
    # Dictionary to track symbols: symbol_name -> [list of packages]
    symbol_to_packages = {}
    # Dictionary to track symbol counts per package
    package_symbol_counts = {}
    
    print("Scanning installed packages for exposed symbols...")
    print()
    
    # Scan all installed packages
    packages = sorted([d.name for d in mip_dir.iterdir() if d.is_dir()])
    
    if not packages:
        print("No packages installed yet")
        return
    
    for package_name in packages:
        package_dir = mip_dir / package_name
        mip_json_path = package_dir / 'mip.json'
        
        # Read mip.json if it exists
        if not mip_json_path.exists():
            package_symbol_counts[package_name] = 0
            continue
        
        try:
            with open(mip_json_path, 'r') as f:
                mip_config = json.load(f)
            
            exposed_symbols = mip_config.get('exposed_symbols', [])
            if not isinstance(exposed_symbols, list):
                exposed_symbols = []
            
            # Track count for this package
            package_symbol_counts[package_name] = len(exposed_symbols)
            
            # Track which packages expose each symbol
            for symbol in exposed_symbols:
                if symbol not in symbol_to_packages:
                    symbol_to_packages[symbol] = []
                symbol_to_packages[symbol].append(package_name)
        
        except Exception as e:
            print(f"Warning: Could not read mip.json for {package_name}: {e}")
            package_symbol_counts[package_name] = 0
    
    # Print symbol counts per package
    print("Exposed symbols per package:")
    for package_name in packages:
        count = package_symbol_counts.get(package_name, 0)
        print(f"  - {package_name}: {count} symbol(s)")
    
    print()
    
    # Find collisions (symbols in more than one package)
    collisions = {symbol: pkgs for symbol, pkgs in symbol_to_packages.items() if len(pkgs) > 1}
    
    if not collisions:
        print("No name collisions found")
    else:
        print(f"Name collisions found: {len(collisions)}")
        print()
        print("Colliding symbols:")
        for symbol in sorted(collisions.keys()):
            packages_list = ', '.join(collisions[symbol])
            print(f"  - {symbol} (found in: {packages_list})")
