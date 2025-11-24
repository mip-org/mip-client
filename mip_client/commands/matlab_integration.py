"""MATLAB integration setup for mip"""

import shutil
from pathlib import Path
from .utils import get_mip_matlab_dir

def _ensure_mip_matlab_setup():
    """Ensure the +mip directory is set up in ~/.mip/matlab
    
    This is called automatically by install, uninstall, and setup commands
    to ensure users always have the latest version of mip.import()
    """
    try:
        # Get the source +mip directory
        source_plus_mip = Path(__file__).parent.parent / 'matlab' / '+mip'
        if not source_plus_mip.exists():
            print("Warning: +mip directory not found in package")
            return
        # Get the source mip.m file
        source_mip_m = Path(__file__).parent.parent / 'matlab' / 'mip.m'
        if not source_mip_m.exists():
            print("Warning: mip.m file not found in package")
            return
        
        # Destination path in ~/.mip/matlab/+mip
        dest_plus_mip = get_mip_matlab_dir() / '+mip'
        
        # Create parent directory if it doesn't exist
        dest_plus_mip.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the +mip directory (remove old one if it exists)
        if dest_plus_mip.exists():
            shutil.rmtree(dest_plus_mip)
        
        shutil.copytree(source_plus_mip, dest_plus_mip)

        # Copy the mip.m file
        dest_mip_m = get_mip_matlab_dir() / 'mip.m'
        shutil.copy2(source_mip_m, dest_mip_m)
        
    except Exception as e:
        print(f"Warning: Failed to update MATLAB integration: {e}")

def setup_matlab():
    """Refresh the +mip directory in ~/.mip/matlab
    
    This ensures you have the latest version of mip.import() after upgrading mip.
    The MATLAB integration is also automatically updated when running install or uninstall commands.
    """
    # Ensure MATLAB integration is up to date
    _ensure_mip_matlab_setup()
    
    home = Path.home()
    mip_matlab_dir = get_mip_matlab_dir()

    print(f"MATLAB integration updated at: {mip_matlab_dir}")
    print(f"\nMake sure to add '{mip_matlab_dir}' to your MATLAB path.")
    print(f"You can do this by running in MATLAB:")
    print(f"  addpath('{mip_matlab_dir}')")
    print(f"  savepath")
