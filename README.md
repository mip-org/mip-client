# mip

> **⚠️ Warning**: This project is at a very early stage of development and is subject to breaking changes.

A simple pip-style package manager for MATLAB packages.

## Installation

Install the package using pip:

```bash
# First, clone the repository
git clone https://github.com/magland/mip.git
cd mip

# Then, install the package
pip install -e .
```


## Setup MATLAB Path

Add `~/.mip/matlab` to your MATLAB path permanently. You can do this in MATLAB:

```matlab
addpath('~/.mip/matlab')
savepath
```

Alternatively, you can add this to your MATLAB `startup.m` file (typically located at `~/Documents/MATLAB/startup.m`):

```matlab
addpath('~/.mip/matlab')
```

**Note**: After upgrading to a new version of mip, run `mip setup` to ensure you have the latest MATLAB integration.

## Usage

### Install a package

```bash
mip install package_name
```

Downloads and installs a package from `https://magland.github.io/mip/package_name-*.mhl` to `~/.mip/packages/package_name`.

### Uninstall a package

```bash
mip uninstall package_name
```

Removes an installed package after confirmation.

Currently, the supported packages are:
- [export_fig](https://github.com/altmany/export_fig)
- [chebfun](https://github.com/chebfun/chebfun)
- [surfacefun](https://github.com/danfortunato/surfacefun) - depends on chebfun
- [FLAM](https://github.com/klho/FLAM)

### List installed packages

```bash
mip list
```

Shows all currently installed packages.

### Using packages in MATLAB

After setting up the MATLAB path and installing packages, you can import them in MATLAB:

```matlab
% Import a package (adds it to the path for the current session)
mip.import('package_name')

% Now you can use the package functions
```

## Package Structure

- Packages are stored in `~/.mip/packages/`
- Each package is extracted from a zip (.mhl) file into its own directory
- The `+mip` MATLAB namespace is installed in `~/.mip/matlab/+mip/`

## Examples

```bash
# Install a package
mip install surfacefun

# List installed packages
mip list

# Use in MATLAB
matlab
>> mip.import('surfacefun')
>> % Now use the toolbox functions

# Uninstall
mip uninstall surfacefun
```

## Requirements

- Python 3.6+
- MATLAB

## Authors

Jeremy Magland and Dan Fortunato - Center for Computational Mathematics, Flatiron Institute

## License

Apache License 2.0
