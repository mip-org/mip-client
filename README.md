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

To set up the MATLAB integration, run:

```bash
mip setup
```

This command will create the necessary directories and files in `~/.mip/matlab` for MATLAB integration.

Then add `~/.mip/matlab` to your MATLAB path permanently. You can do this in MATLAB:

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

Either from the command line or from within MATLAB, run:

```bash
mip install package_name
```

Downloads and installs a package to `~/.mip/packages/package_name`.

Currently, the supported packages are:
- [export_fig](https://github.com/altmany/export_fig)
- [chebfun](https://github.com/chebfun/chebfun)
- [surfacefun](https://github.com/danfortunato/surfacefun) - depends on chebfun
- [FLAM](https://github.com/klho/FLAM)
- [kdtree](https://github.com/taiya/kdtree) - however, Linux MEX files are not yet provided
- [fmm2d](https://github.com/flatironinstitute/fmm2d) - however, only Linux MEX files are currently provided

### Using packages in MATLAB

After setting up the MATLAB path and installing packages, you can import them in MATLAB:

```matlab
% Import a package (adds it to the path for the current session)
mip.import('package_name')

% or
mip import package_name

% Now you can use the package functions
```

### List installed packages

```bash
mip list
```

Shows all currently installed packages.

### Uninstall a package

```bash
mip uninstall package_name
```

Removes an installed package after confirmation. Also removes any packages that depend on it.

## Internal Package Structure

- Packages are stored in `~/.mip/packages/`
- Each package is extracted from a zip (.mhl) file into its own directory
- Each package has a `mip.json` file containing metadata and a `setup.m` that gets called on import
- The `+mip` MATLAB namespace is installed in `~/.mip/matlab/+mip/`

## Example

```bash
# Install a package
mip install surfacefun

# List installed packages
mip list

# Use in MATLAB
matlab
>> mip import surfacefun
>> % Now use the toolbox functions

# Uninstall
mip uninstall surfacefun
```

## How to add new packages

For now mip supports a very limited set of packages, which are built as part of this repository. To add a new package, you should submit a pull request to https://github.com/mip-org/mip-core.

## Requirements

- Python 3.6+
- MATLAB

## Authors

Jeremy Magland and Dan Fortunato - Center for Computational Mathematics, Flatiron Institute

## License

Apache License 2.0
