#!/usr/bin/env python3
import requests
import os
import zipfile
import shutil
import tempfile

def main():
    url = "https://github.com/altmany/export_fig/archive/refs/tags/v3.54.zip"
    download_file = "export_fig_download.zip"
    version = "3.54"
    # Follow Python wheel naming convention: {package}-{version}-{matlab_tag}-{abi_tag}-{platform_tag}.mhl
    output_file = f"export_fig-{version}-any-none-any.mhl"
    
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
        
        # Move export_fig-3.54 to the build directory (keep the version in the name)
        extracted_dir = os.path.join(temp_dir, f"export_fig-{version}")
        export_fig_dir = os.path.join(mhl_build_dir, f"export_fig-{version}")
        print(f"Moving export_fig-{version}...")
        shutil.move(extracted_dir, export_fig_dir)
        
        # Create setup.m file
        setup_m_path = os.path.join(mhl_build_dir, "setup.m")
        print("Creating setup.m...")
        with open(setup_m_path, 'w') as f:
            f.write("% Add export_fig to the MATLAB path\n")
            f.write(f"export_fig_path = fullfile(fileparts(mfilename('fullpath')), 'export_fig-{version}');\n")
            f.write("addpath(export_fig_path);\n")
        
        # Create the .mhl file (which is a zip file)
        print(f"Creating {output_file}...")
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as mhl_zip:
            # Add setup.m
            mhl_zip.write(setup_m_path, 'setup.m')
            
            # Add all files in the export_fig directory
            for root, dirs, files in os.walk(export_fig_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, mhl_build_dir)
                    mhl_zip.write(file_path, arcname)
    
    # Clean up downloaded zip
    os.remove(download_file)
    
    print(f"Created {output_file} successfully!")

if __name__ == "__main__":
    main()
