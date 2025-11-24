"""Command implementations for mip - modular structure

This package contains the command implementations split into logical modules.
Public functions are re-exported here for backward compatibility.
"""

# Import public command functions
from .install import install_package
from .uninstall import uninstall_package
from .list_command import list_packages
from .find_collisions import find_name_collisions
from .matlab_integration import setup_matlab

# Export public API
__all__ = [
    'install_package',
    'uninstall_package',
    'list_packages',
    'find_name_collisions',
    'setup_matlab',
]
