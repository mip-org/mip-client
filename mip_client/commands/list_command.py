"""List installed packages command"""

import json
from .utils import get_mip_packages_dir

def list_packages():
    """List all installed packages with their versions"""
    mip_dir = get_mip_packages_dir()
    
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
                print(f"  - {package} ({version})")
            else:
                print(f"  - {package}")
