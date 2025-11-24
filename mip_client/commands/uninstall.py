"""Package uninstallation functionality"""

import sys
import shutil

from .utils import get_mip_packages_dir
from .matlab_integration import _ensure_mip_matlab_setup
from .package_info import _read_package_dependencies
from .dependency_graph import _find_reverse_dependencies, _build_uninstall_order

def uninstall_package(package_names):
    """Uninstall one or more packages and all packages that depend on them
    
    Args:
        package_names: Package name(s) to uninstall. Can be:
                      - A single string (package name)
                      - A list of strings (multiple packages)
    """
    # Ensure MATLAB integration is up to date
    _ensure_mip_matlab_setup()
    
    mip_dir = get_mip_packages_dir()
    
    # Normalize input to a list
    if isinstance(package_names, str):
        package_names = [package_names]
    
    # Phase 1: Validate and build uninstallation plan
    
    # Check which requested packages are installed
    not_installed = []
    requested_packages = []
    
    for pkg_name in package_names:
        package_dir = mip_dir / pkg_name
        if not package_dir.exists():
            not_installed.append(pkg_name)
        else:
            requested_packages.append(pkg_name)
    
    # Report packages that aren't installed
    if not_installed:
        for pkg_name in not_installed:
            print(f"Package '{pkg_name}' is not installed")
    
    # If no valid packages to uninstall, return
    if not requested_packages:
        return
    
    # Find all packages that depend on any of the requested packages
    if len(requested_packages) == 1:
        print(f"Scanning for packages that depend on '{requested_packages[0]}'...")
    else:
        print(f"Scanning for packages that depend on {len(requested_packages)} packages...")
    
    all_to_uninstall = set(requested_packages)
    
    for pkg_name in requested_packages:
        reverse_deps = _find_reverse_dependencies(pkg_name, mip_dir)
        all_to_uninstall.update(reverse_deps)
    
    # Sort packages in proper uninstallation order
    to_uninstall = _build_uninstall_order(all_to_uninstall, mip_dir)
    
    # Display uninstallation plan
    if len(to_uninstall) > 1:
        print(f"\nThe following packages will be uninstalled:")
        
        for pkg in to_uninstall:
            if pkg in requested_packages:
                print(f"  - {pkg}")
            else:
                # Find which requested packages this depends on
                depends_on = []
                pkg_deps = _read_package_dependencies(mip_dir / pkg)
                for requested in requested_packages:
                    if requested in pkg_deps:
                        depends_on.append(requested)
                    else:
                        # Check transitive dependencies
                        all_deps = set()
                        to_check = list(pkg_deps)
                        checked = set()
                        while to_check:
                            dep = to_check.pop(0)
                            if dep in checked or dep not in all_to_uninstall:
                                continue
                            checked.add(dep)
                            all_deps.add(dep)
                            dep_dir = mip_dir / dep
                            if dep_dir.exists():
                                to_check.extend(_read_package_dependencies(dep_dir))
                        
                        if requested in all_deps:
                            depends_on.append(requested)
                
                if depends_on:
                    print(f"  - {pkg} (depends on {', '.join(depends_on)})")
                else:
                    print(f"  - {pkg}")
        print()
    
    # Confirm uninstallation
    if len(to_uninstall) == 1:
        response = input(f"Are you sure you want to uninstall '{to_uninstall[0]}'? (y/n): ")
    else:
        response = input(f"Are you sure you want to uninstall these {len(to_uninstall)} packages? (y/n): ")
    
    if response.lower() not in ['y', 'yes']:
        print("Uninstallation cancelled")
        return
    
    # Phase 2: Execute uninstallations
    print()
    uninstalled_count = 0
    
    for pkg in to_uninstall:
        pkg_dir = mip_dir / pkg
        if pkg_dir.exists():
            try:
                print(f"Uninstalling '{pkg}'...")
                shutil.rmtree(pkg_dir)
                print(f"Successfully uninstalled '{pkg}'")
                uninstalled_count += 1
            except Exception as e:
                print(f"Error: Failed to uninstall package '{pkg}': {e}")
                sys.exit(1)
    
    print(f"\nSuccessfully uninstalled {uninstalled_count} package(s)")
