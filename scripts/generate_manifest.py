#!/usr/bin/env python3
"""Generate packages.json manifest from .mhl files"""

import json
import os
import zipfile
import sys
from pathlib import Path

def extract_package_info(mhl_path):
    """Extract package information from an .mhl file"""
    filename = os.path.basename(mhl_path)
    
    # Parse filename: {package}-{version}-{matlab_tag}-{abi_tag}-{platform_tag}.mhl
    parts = filename.replace('.mhl', '').split('-')
    
    if len(parts) < 5:
        print(f"Warning: Unexpected filename format: {filename}", file=sys.stderr)
        return None
    
    package_name = parts[0]
    version = parts[1]
    
    # Try to extract dependencies from mip.json inside the .mhl
    dependencies = []
    try:
        with zipfile.ZipFile(mhl_path, 'r') as mhl_zip:
            if 'mip.json' in mhl_zip.namelist():
                with mhl_zip.open('mip.json') as f:
                    mip_config = json.load(f)
                    dependencies = mip_config.get('dependencies', [])
    except Exception as e:
        print(f"Warning: Could not read mip.json from {filename}: {e}", file=sys.stderr)
    
    return {
        "name": package_name,
        "filename": filename,
        "version": version,
        "dependencies": dependencies
    }

def main():
    # Look for .mhl files in the packages directory
    packages_dir = Path("deploy/packages")
    
    if not packages_dir.exists():
        print("Error: deploy/packages directory not found", file=sys.stderr)
        sys.exit(1)
    
    mhl_files = sorted(packages_dir.glob("*.mhl"))
    
    if not mhl_files:
        print("Error: No .mhl files found in deploy/packages", file=sys.stderr)
        sys.exit(1)
    
    # Extract info from each package
    packages = []
    for mhl_path in mhl_files:
        package_info = extract_package_info(mhl_path)
        if package_info:
            packages.append(package_info)
    
    packages.append({
        "name": "fmm2d",
        "filename": "http://users.flatironinstitute.org/~magland/mip/packages/fmm2d-latest-any-none-any.mhl",
        "version": "latest",
        "dependencies": []
    })
    
    # Create manifest
    manifest = {
        "packages": packages
    }
    
    # Write to deploy/packages.json
    output_path = Path("deploy/packages.json")
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Generated {output_path} with {len(packages)} packages")
    
    # Print summary
    for pkg in packages:
        deps_str = f" (depends on: {', '.join(pkg['dependencies'])})" if pkg['dependencies'] else ""
        print(f"  - {pkg['name']} v{pkg['version']}{deps_str}")

if __name__ == "__main__":
    main()