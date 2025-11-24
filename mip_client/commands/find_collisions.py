"""Find name collisions command"""

import json
from .utils import get_mip_packages_dir

def find_name_collisions():
    """Find and report name collisions in exposed symbols across all installed packages"""
    mip_dir = get_mip_packages_dir()
    
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
