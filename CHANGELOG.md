# Change Log

## Unreleased

## [0.3.2] - 2025-12-20

- platform -> architecture renaming (including mip architecture command)

## [0.3.1] - 2025-11-27

- Fix bug when installing from local .mhl file

## [0.3.0] - 2025-11-26

- Use load_package.m and unload_package.m instead of load.m and unload.m for package-specific load/unload functions

## [0.2.0] - 2025-11-24

- Direct/indirect imports and listing imported packages
- pin/unpin packages and unimport --all
- rename import -> load, unimport -> unload

## [0.1.4] - 2025-11-24

- Split commands.py into multiple files
- Support architecture-specific package versions
- Allow MIP_DIR environment variable to override default packages directory location

## [0.1.3] - 2025-11-22

- Moved +mip and mip.m in source tree to matlab/+mip and matlab/mip.m
- In import.m, determine location of packages directory relative to location of current script file
- Allow installing multiple packages at once via `mip install package1 package2 ...`
- Allow uninstalling multiple packages at once

## [0.1.2] - 2025-11-22