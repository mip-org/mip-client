#!/usr/bin/env python3
import subprocess
import shutil
import os
import zipfile
import tempfile
from build_helpers import create_mip_json

def collect_kdtree_symbols(toolbox_dir):
    """
    Collect exposed symbols from kdtree toolbox directory.
    Includes both .m and .cpp files.
    
    Args:
        toolbox_dir: The toolbox directory to scan
    
    Returns:
        List of symbol names
    """
    symbols = []
    
    if not os.path.exists(toolbox_dir):
        return symbols
    
    items = os.listdir(toolbox_dir)
    
    for item in sorted(items):
        item_path = os.path.join(toolbox_dir, item)
        
        if os.path.isfile(item_path):
            # Add .m files
            if item.endswith('.m'):
                symbols.append(item[:-2])  # Remove .m extension
            # Add .cpp files
            elif item.endswith('.cpp'):
                symbols.append(item[:-4])  # Remove .cpp extension
    
    return symbols

def main():
    repo_url = "https://github.com/taiya/kdtree.git"
    clone_dir = "kdtree"
    # Follow Python wheel naming convention: {package}-{version}-{matlab_tag}-{abi_tag}-{platform_tag}.mhl
    output_file = "kdtree-latest-any-none-any.mhl"
    
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
    
    # Remove .git directories to reduce size
    print("Removing .git directories...")
    for root, dirs, files in os.walk(clone_dir):
        if ".git" in dirs:
            git_dir = os.path.join(root, ".git")
            shutil.rmtree(git_dir)
            dirs.remove(".git")
    
    # Create a temporary directory for building the .mhl
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the .mhl structure directory
        mhl_build_dir = os.path.join(temp_dir, "mhl_build")
        os.makedirs(mhl_build_dir)
        
        # Copy toolbox directory to kdtree directory
        toolbox_src = os.path.join(clone_dir, "toolbox")
        kdtree_dest = os.path.join(mhl_build_dir, "kdtree")
        print(f"Copying toolbox directory to kdtree...")
        shutil.copytree(toolbox_src, kdtree_dest)
        
        # Compile MEX files using kdtree_compile.m
        print("Compiling MEX files using kdtree_compile.m...")
        compile_command = f"cd('{kdtree_dest}'); kdtree_compile"
        subprocess.run(
            ["matlab", "-batch", compile_command],
            check=True
        )
        
        # Collect exposed symbols from kdtree directory (including .cpp files)
        print("Collecting exposed symbols...")
        exposed_symbols = collect_kdtree_symbols(kdtree_dest)
        
        # Create setup.m file
        setup_m_path = os.path.join(mhl_build_dir, "setup.m")
        print("Creating setup.m...")
        with open(setup_m_path, 'w') as f:
            f.write("% Add kdtree to the MATLAB path\n")
            f.write("kdtree_path = fullfile(fileparts(mfilename('fullpath')), 'kdtree');\n")
            f.write("addpath(kdtree_path);\n")
        
        # Create mip.json with no dependencies and exposed_symbols
        mip_json_path = os.path.join(mhl_build_dir, "mip.json")
        print("Creating mip.json with exposed_symbols...")
        create_mip_json(mip_json_path, dependencies=[], exposed_symbols=exposed_symbols)
        
        # Create the .mhl file (which is a zip file)
        print(f"Creating {output_file}...")
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as mhl_zip:
            # Add setup.m
            mhl_zip.write(setup_m_path, 'setup.m')
            
            # Add mip.json
            mhl_zip.write(mip_json_path, 'mip.json')
            
            # Add all files in the kdtree directory
            for root, dirs, files in os.walk(kdtree_dest):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, mhl_build_dir)
                    mhl_zip.write(file_path, arcname)
    
    # Clean up clone directory
    print(f"Cleaning up {clone_dir}...")
    shutil.rmtree(clone_dir)
    
    print(f"Created {output_file} successfully!")

if __name__ == "__main__":
    main()
