"""Utility functions for mip"""

from pathlib import Path


def get_mip_dir():
    """Get the mip packages directory path"""
    home = Path.home()
    return home / '.mip' / 'packages'
