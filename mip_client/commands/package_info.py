"""Functions for reading package information from mip.json"""

import json
from pathlib import Path

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
