#!/usr/bin/env python3
import subprocess
import shutil
import os
import zipfile
import tempfile

def main():
    repo_url = "https://github.com/danfortunato/surfacefun.git"
    clone_dir = "surfacefun"
    # Follow Python wheel naming convention: {package}-{version}-{matlab_tag}-{abi_tag}-{platform_tag}.mhl
    output_file = "surfacefun-latest-any-none-any.mhl"
    
    # Remove clone directory if it exists
    if os.path.exists(clone_dir):
        print(f"Removing existing {clone_dir} directory...")
        shutil.rmtree(clone_dir)
    
    # Clone the repository with submodules
    print(f"Cloning {repo_url} with submodules...")
    subprocess.run(
        ["git", "clone", "--recurse-submodules", repo_url],
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
        
        # Move surfacefun to the build directory
        surfacefun_dir = os.path.join(mhl_build_dir, "surfacefun")
        print(f"Moving surfacefun...")
        shutil.move(clone_dir, surfacefun_dir)
        
        # Create setup.m file
        setup_m_path = os.path.join(mhl_build_dir, "setup.m")
        print("Creating setup.m...")
        with open(setup_m_path, 'w') as f:
            f.write("% Add surfacefun to the MATLAB path and run setup\n")
            f.write("surfacefun_path = fullfile(fileparts(mfilename('fullpath')), 'surfacefun');\n")
            f.write("addpath(surfacefun_path);\n")
            f.write("setup_file = fullfile(surfacefun_path, 'setup.m');\n")
            f.write("if exist(setup_file, 'file')\n")
            f.write("    run(setup_file);\n")
            f.write("end\n")
        
        # Create mip.json with dependencies
        mip_json_path = os.path.join(mhl_build_dir, "mip.json")
        print("Creating mip.json with dependencies...")
        import json
        mip_config = {
            "dependencies": ["chebfun"]
        }
        with open(mip_json_path, 'w') as f:
            json.dump(mip_config, f, indent=2)
        
        # Create the .mhl file (which is a zip file)
        print(f"Creating {output_file}...")
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as mhl_zip:
            # Add setup.m
            mhl_zip.write(setup_m_path, 'setup.m')
            
            # Add mip.json
            mhl_zip.write(mip_json_path, 'mip.json')
            
            # Add all files in the surfacefun directory
            for root, dirs, files in os.walk(surfacefun_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, mhl_build_dir)
                    mhl_zip.write(file_path, arcname)
    
    print(f"Created {output_file} successfully!")

if __name__ == "__main__":
    main()
