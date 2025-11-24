"""Utility functions for mip"""

import os
from pathlib import Path


def get_mip_dir():
    """Get the mip directory path"""
    mip_dir = os.environ.get('MIP_DIR')
    if mip_dir:
        return Path(mip_dir)
    home = Path.home()
    return home / '.mip'

def get_mip_packages_dir():
    """Get the mip packages directory path"""
    return get_mip_dir() / 'packages'

def get_mip_matlab_dir():
    """Get the mip MATLAB integration directory path"""
    return get_mip_dir() / 'matlab'
