#!/usr/bin/env python3
import subprocess
import shutil
import os
import zipfile
import tempfile
from build_helpers import create_mip_json

def collect_exposed_symbols_with_c_files(package_dir):
    """
    Collect exposed symbols from the top level of a directory,
    including .m files, .c files, + and @ directories.
    
    Args:
        package_dir: The directory to scan
    
    Returns:
        List of symbol names
    """
    symbols = []
    
    if not os.path.exists(package_dir):
        return symbols
    
    items = os.listdir(package_dir)
    
    for item in sorted(items):
        item_path = os.path.join(package_dir, item)
        
        if item.endswith('.m') and os.path.isfile(item_path):
            # Add .m file (without extension)
            symbols.append(item[:-2])
        elif item.endswith('.c') and os.path.isfile(item_path):
            # Add .c file (without extension)
            symbols.append(item[:-2])
        elif os.path.isdir(item_path) and (item.startswith('+') or item.startswith('@')):
            # Add package or class directory (without + or @)
            symbols.append(item[1:])
    
    return symbols

def main():
    repo_url = "https://github.com/flatironinstitute/fmm2d.git"
    clone_dir = "fmm2d"
    output_file = "fmm2d-latest-any-none-any.mhl"
    
    # Remove clone directory if it exists
    if os.path.exists(clone_dir):
        print(f"Removing existing {clone_dir} directory...")
        shutil.rmtree(clone_dir)
    
    # Clone the repository
    print(f"Cloning {repo_url}...")
    subprocess.run(
        ["git", "clone", repo_url],
        check=True
    )
    
    # Modify Makefile to replace -march=native with -march=x86-64
    print("Modifying Makefile to use -march=x86-64...")
    makefile_path = os.path.join(clone_dir, "Makefile")
    if not os.path.exists(makefile_path):
        raise RuntimeError(f"Makefile not found at {makefile_path}")
    
    with open(makefile_path, 'r') as f:
        makefile_content = f.read()
    
    if '-march=native' not in makefile_content:
        raise RuntimeError("Could not find '-march=native' in Makefile")
    
    modified_content = makefile_content.replace('-march=native', '-march=x86-64')
    
    with open(makefile_path, 'w') as f:
        f.write(modified_content)
    
    print("Makefile modified successfully")
    
    # Run 'make matlab' in the cloned directory
    print("Running 'make matlab'...")
    subprocess.run(
        ["make", "matlab"],
        cwd=clone_dir,
        check=True
    )
    
    # Check if matlab/ directory was created
    matlab_dir = os.path.join(clone_dir, "matlab")
    if not os.path.exists(matlab_dir):
        raise RuntimeError(f"Expected {matlab_dir} to be created by 'make matlab'")
    
    # Remove .git directory to reduce size
    print("Removing .git directory...")
    git_dir = os.path.join(clone_dir, ".git")
    if os.path.exists(git_dir):
        shutil.rmtree(git_dir)
    
    # Create a temporary directory for building the .mhl
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the .mhl structure directory
        mhl_build_dir = os.path.join(temp_dir, "mhl_build")
        os.makedirs(mhl_build_dir)
        
        # Copy matlab/ directory contents to fmm2d/ in the build directory
        fmm2d_dir = os.path.join(mhl_build_dir, "fmm2d")
        print(f"Copying matlab/ directory to fmm2d/...")
        shutil.copytree(matlab_dir, fmm2d_dir)
        
        # Collect exposed symbols from fmm2d directory (top level, including .c files)
        print("Collecting exposed symbols...")
        exposed_symbols = collect_exposed_symbols_with_c_files(fmm2d_dir)
        
        # Create setup.m file
        setup_m_path = os.path.join(mhl_build_dir, "setup.m")
        print("Creating setup.m...")
        with open(setup_m_path, 'w') as f:
            f.write("% Add fmm2d to the MATLAB path\n")
            f.write("fmm2d_path = fullfile(fileparts(mfilename('fullpath')), 'fmm2d');\n")
            f.write("addpath(fmm2d_path);\n")
        
        # Create mip.json with package name and exposed_symbols (no dependencies)
        mip_json_path = os.path.join(mhl_build_dir, "mip.json")
        print("Creating mip.json with package name and exposed_symbols...")
        create_mip_json(mip_json_path, package_name="fmm2d", dependencies=[], exposed_symbols=exposed_symbols)
        
        # Create the .mhl file (which is a zip file)
        print(f"Creating {output_file}...")
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as mhl_zip:
            # Add setup.m
            mhl_zip.write(setup_m_path, 'setup.m')
            
            # Add mip.json
            mhl_zip.write(mip_json_path, 'mip.json')
            
            # Add all files in the fmm2d directory
            for root, dirs, files in os.walk(fmm2d_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, mhl_build_dir)
                    mhl_zip.write(file_path, arcname)
    
    # Clean up the cloned directory
    print(f"Cleaning up {clone_dir} directory...")
    shutil.rmtree(clone_dir)
    
    print(f"Created {output_file} successfully!")

if __name__ == "__main__":
    main()
