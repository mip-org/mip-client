"""Dependency graph operations for package management"""

import sys
from .package_info import _read_package_dependencies

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

def _topological_sort_packages(package_names, package_info_map):
    """Sort packages in topological order (dependencies first)
    
    Args:
        package_names: List of package names to sort
        package_info_map: Dictionary mapping package names to their info
    
    Returns:
        List of package names in topological order
    """
    # Build adjacency list (package -> list of packages it depends on)
    dependencies = {}
    for pkg_name in package_names:
        pkg_info = package_info_map.get(pkg_name)
        if pkg_info:
            dependencies[pkg_name] = pkg_info.get('dependencies', [])
        else:
            dependencies[pkg_name] = []
    
    # Topological sort using DFS
    visited = set()
    result = []
    
    def visit(pkg_name):
        if pkg_name in visited:
            return
        visited.add(pkg_name)
        
        # Visit dependencies first
        for dep in dependencies.get(pkg_name, []):
            if dep in package_names:  # Only visit if it's in our list
                visit(dep)
        
        result.append(pkg_name)
    
    for pkg_name in package_names:
        visit(pkg_name)
    
    return result

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

def _build_uninstall_order(packages_to_uninstall, mip_dir):
    """Sort packages in reverse topological order for uninstallation
    
    Packages with reverse dependencies should be uninstalled first,
    then packages they depend on.
    
    Args:
        packages_to_uninstall: Set of package names to uninstall
        mip_dir: The mip directory path
    
    Returns:
        List of package names in uninstallation order
    """
    # Build dependency graph for packages to uninstall
    dependencies = {}
    for pkg_name in packages_to_uninstall:
        pkg_dir = mip_dir / pkg_name
        dependencies[pkg_name] = _read_package_dependencies(pkg_dir)
    
    # Topological sort - but we want reverse order for uninstallation
    # (packages with no dependents first, then their dependencies)
    visited = set()
    result = []
    
    def visit(pkg_name):
        if pkg_name in visited:
            return
        visited.add(pkg_name)
        
        # Visit packages that depend on this one first (from our uninstall set)
        for other_pkg in packages_to_uninstall:
            if other_pkg != pkg_name and pkg_name in dependencies.get(other_pkg, []):
                visit(other_pkg)
        
        result.append(pkg_name)
    
    for pkg_name in packages_to_uninstall:
        visit(pkg_name)
    
    return result
