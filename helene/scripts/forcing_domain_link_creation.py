## Create forcing soft links for the NADaymet/TESSFA cases

import os
import glob
import shutil

path = "../atm_forcing.datm7.km.1d"

# Check if the directory exists
if os.path.isdir(path):
    # If it exists, remove it
    shutil.rmtree(path)

# Create a new folder
os.makedirs(path)
# Change to the new directory
os.chdir(path)

# Get a list of all files in the forcing directory and its subdirectories
files = glob.glob('../forcing/**/*', recursive=True)

# Loop through the files
for file in files:
    # Check if 'clmforc' is in the file name
    if 'clmforc' in file:
        # Split the file name on '_'
        parts = os.path.basename(file).split('_')

        # Check if there is at least one underscore and construct the link name
        if len(parts) > 1:
            # Join parts[1:] back together with '_' to form the new link name
            link_name = '_'.join(parts[1:])
        else:
            link_name = os.path.basename(file)

        prefix = "clmforc."
        suffix = ".1d"
        replacement = "Daymet.km"

        # Find the start and end indices for slicing
        start_index = len(prefix)  # Length of "clmforc."
        end_index = link_name.find(suffix)  # Find where ".1d" is located

        # Construct the new link_name
        new_link_name = link_name[:start_index] + replacement + link_name[end_index:]

        # Create a soft link in the target directory
        link_path = os.path.join(path, new_link_name)

        #command = f'ln -s "{file}" "{link_path}"'
        #print(command)

        # Only create the link if it does not already exist
        if not os.path.exists(link_path):
            command = f'ln -s "{file}" "{link_path}"'
            print(command)
            os.system(command)
        else:
            print(f"Link {link_path} already exists, skipping.")

files = glob.glob('../domain_surfdata/*')
for file in files:
    print(file)
    # Check if 'domain' is in the file name
    if '_domain.lnd' in file:
        # Construct the new link_name
        new_link_name = "domain.lnd.Daymet.km.1d.nc"
        # Create a soft link in the target directory
        link_path = os.path.join(path, new_link_name)

        # Only create the link if it does not already exist
        if not os.path.exists(link_path):
            command = f'ln -s "{file}" "{link_path}"'
            print(command)
            os.system(command)
        else:
            print(f"Link {link_path} already exists, skipping.")


print("Soft links created successfully.")
