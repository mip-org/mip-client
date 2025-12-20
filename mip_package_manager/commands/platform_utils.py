"""Platform detection and compatibility utilities"""

import platform
import sys


def get_current_architecture_tag():
    """Detect the current architecture and return the corresponding MIP architecture tag

    Returns:
        str: Architecture tag (e.g., 'linux_x86_64', 'macosx_11_0_arm64', 'win_amd64')
    """
    system = platform.system()
    machine = platform.machine().lower()
    
    # Normalize machine architecture names
    if machine in ('x86_64', 'amd64'):
        machine = 'x86_64'
    elif machine in ('aarch64', 'arm64'):
        machine = 'aarch64' if system == 'Linux' else 'arm64'
    elif machine in ('i386', 'i686'):
        machine = 'i686'
    
    if system == 'Linux':
        if machine == 'x86_64':
            return 'linux_x86_64'
        elif machine == 'aarch64':
            return 'linux_aarch64'
        elif machine == 'i686':
            return 'linux_i686'
        else:
            return f'linux_{machine}'
    
    elif system == 'Darwin':  # macOS
        if machine == 'x86_64':
            return 'macosx_10_9_x86_64'
        elif machine == 'arm64':
            return 'macosx_11_0_arm64'
        else:
            return f'macosx_10_9_{machine}'
    
    elif system == 'Windows':
        if machine == 'x86_64':
            return 'win_amd64'
        elif machine == 'arm64':
            return 'win_arm64'
        elif machine == 'i686':
            return 'win32'
        else:
            return f'win_{machine}'
    
    else:
        # Unknown architecture - return a generic tag
        return f'{system.lower()}_{machine}'


def is_architecture_compatible(package_architecture, current_architecture=None):
    """Check if a package's architecture tag is compatible with the current architecture
    
    Args:
        package_architecture: The architecture tag from the package metadata
        current_architecture: The current architecture tag (detected if not provided)
    
    Returns:
        bool: True if compatible, False otherwise
    """
    if current_architecture is None:
        current_architecture = get_current_architecture_tag()

    # Universal packages work on any architecture
    if package_architecture == 'any':
        return True
    
    # Exact match
    if package_architecture == current_architecture:
        return True
    
    # Special case: macOS universal2 binaries work on both Intel and Apple Silicon
    if package_architecture == 'macosx_10_9_universal2':
        if current_architecture in ('macosx_10_9_x86_64', 'macosx_11_0_arm64'):
            return True
    
    return False


def select_best_package_variant(variants, current_architecture=None):
    """Select the best package variant for the current architecture

    When multiple variants of a package exist (e.g., architecture-specific and 'any'),
    prefer the architecture-specific version.

    Args:
        variants: List of package info dictionaries with 'architecture' field
        current_architecture: The current architecture (detected if not provided)

    Returns:
        dict or None: The best matching package variant, or None if no compatible variant
    """
    if current_architecture is None:
        current_architecture = get_current_architecture_tag()
    
    if not variants:
        return None
    
    # Filter to compatible variants only
    for v in variants:
        if 'architecture' not in v:
            print(v)
            print(f"Warning: Package variant {v.get('name', '<unknown>')} is missing 'architecture' field")
            v['architecture'] = 'error_missing_field'
    compatible = [v for v in variants if is_architecture_compatible(v['architecture'], current_architecture)]

    if not compatible:
        return None

    # Prefer exact architecture matches over 'any'
    exact_matches = [v for v in compatible if v['architecture'] == current_architecture]
    if exact_matches:
        # If multiple exact matches, prefer the one with highest version/build
        return exact_matches[0]
    
    # Check for universal2 on macOS
    if current_architecture.startswith('macosx_'):
        universal2 = [v for v in compatible if v['architecture'] == 'macosx_10_9_universal2']
        if universal2:
            return universal2[0]

    # Fall back to 'any' architecture
    any_architecture = [v for v in compatible if v['architecture'] == 'any']
    if any_architecture:
        return any_architecture[0]

    # Should not reach here if is_architecture_compatible is working correctly
    return compatible[0] if compatible else None


def get_available_architectures_for_package(variants):
    """Get a list of available architectures for a package

    Args:
        variants: List of package info dictionaries with 'architecture' field

    Returns:
        list: Sorted list of unique architecture tags
    """
    architectures = set(v['architecture'] for v in variants)
    return sorted(architectures)

def print_architecture():
    """Print the current architecture tag"""
    architecture_tag = get_current_architecture_tag()
    print(f"{architecture_tag}")
