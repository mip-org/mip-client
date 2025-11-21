#!/usr/bin/env python3
import requests
import os
import zipfile
import shutil
import tempfile

def main():
    url = "https://github.com/chebfun/chebfun/archive/master.zip"
    download_file = "chebfun_download.zip"
    # Follow Python wheel naming convention: {package}-{version}-{python_tag}-{abi_tag}-{platform_tag}.whl
    # Adapted for MATLAB: {package}-{version}-{matlab_tag}-{abi_tag}-{platform_tag}.mhl
    output_file = "chebfun-latest-any-none-any.mhl"
    
    # Download the zip file
    print(f"Downloading {url}...")
    response = requests.get(url)
    response.raise_for_status()
    
    with open(download_file, 'wb') as f:
        f.write(response.content)
    print("Download complete.")
    
    # Create a temporary directory for building the .mhl
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Extracting downloaded zip...")
        with zipfile.ZipFile(download_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Create the .mhl structure directory
        mhl_build_dir = os.path.join(temp_dir, "mhl_build")
        os.makedirs(mhl_build_dir)
        
        # Move chebfun-master to chebfun in the build directory
        extracted_dir = os.path.join(temp_dir, "chebfun-master")
        chebfun_dir = os.path.join(mhl_build_dir, "chebfun")
        print(f"Moving chebfun-master to chebfun...")
        shutil.move(extracted_dir, chebfun_dir)
        
        # Create setup.m file
        setup_m_path = os.path.join(mhl_build_dir, "setup.m")
        print("Creating setup.m...")
        with open(setup_m_path, 'w') as f:
            f.write("% Add chebfun to the MATLAB path\n")
            f.write("chebfun_path = fullfile(fileparts(mfilename('fullpath')), 'chebfun');\n")
            f.write("addpath(chebfun_path);\n")
        
        # Create the .mhl file (which is a zip file)
        print(f"Creating {output_file}...")
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as mhl_zip:
            # Add setup.m
            mhl_zip.write(setup_m_path, 'setup.m')
            
            # Add all files in the chebfun directory
            for root, dirs, files in os.walk(chebfun_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, mhl_build_dir)
                    mhl_zip.write(file_path, arcname)
    
    # Clean up downloaded zip
    os.remove(download_file)
    
    print(f"Created {output_file} successfully!")

if __name__ == "__main__":
    main()
