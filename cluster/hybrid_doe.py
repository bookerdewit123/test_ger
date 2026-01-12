import itertools
import csv
import os
import sys
import random
import math
import time
import platform
import glob
from itertools import product
import subprocess
import pathlib

local_location = str(pathlib.Path(__file__).parent.resolve())

afsim_location = r'C:\AFSIM\AFSIM-2.2205.6+lts-x64-windows\AFSIM-2.2205.6+lts-x64-windows\bin\mission.exe' #Local Path to AFSIM 2.2205.6+lts mission.exe file
linux_afsim_location = r'../../../../../AFSIM-2.2205.6+lts-x64-linux/bin/mission' 

csv_file = local_location +r"\doe.csv"  # Replace with your actual CSV file path
seeds_csv = local_location +r"\random_seeds.csv"  # Replace with your actual CSV file path for random seeds
cluster_dir = local_location +r"\cluster_runs"  # Specify the output directory
num_runs = 10  # Specify how many files and runs we want to generate

def generate_random_files(data_csv, seeds_csv, num_runs, cluster_dir):
    # Initialize lists to store headers and their associated values
    headers = []
    header_data = []
    excursion_options = []
    vignette_options = []

    # Read the data CSV file
    with open(data_csv, mode='r') as file:
        reader = csv.reader(file)

        for row in reader:
            if row:  # Ensure the row is not empty
                if row[0].strip() == "EXCURSION":
                    excursion_options = [value.strip() for value in row[1:] if value.strip()]
                elif row[0].strip() == "VIGNETTE":
                    vignette_options = [value.strip() for value in row[1:] if value.strip()]
                else:
                    headers.append(row[0].strip())  # First column as header
                    header_data.append([value.strip() for value in row[1:] if value.strip()])

    # Read the random seeds CSV file
    with open(seeds_csv, mode='r') as file:
        seeds_reader = csv.reader(file)
        seeds = [row[0].strip() for row in seeds_reader if row]  # Clean values

    # Create output directory if it does not exist
    os.makedirs(cluster_dir, exist_ok=True)

    # Define the base directory for Outputs
    base_dir_strike = os.path.join('C:\\Users', os.getenv('USERNAME'), 'output', 'DCA', 'Strike')
    base_dir_multi_axis = os.path.join('C:\\Users', os.getenv('USERNAME'), 'output', 'DCA', 'MultiAxis')
    base_dir_sead = os.path.join('C:\\Users', os.getenv('USERNAME'), 'output', 'SEAD')
    
    # Create the main Strike and Multi Axis directory and subdirectories for Baseline and Excursions
    subfolders = ['Baseline'] + [f'Excursion {i}' for i in range(1, 8)]  # Excursions 1-7
    for subfolder in subfolders:
        os.makedirs(os.path.join(base_dir_strike, subfolder), exist_ok=True)
        os.makedirs(os.path.join(base_dir_multi_axis, subfolder), exist_ok=True)

    # Create SEAD directory and Vignettes subdirectories
    vignettes_subfolders = ['Vignette 1', 'Vignette 2', 'Vignette 3']
    os.makedirs(base_dir_sead, exist_ok=True)  # Create SEAD directory
    for vignettes in vignettes_subfolders:
        os.makedirs(os.path.join(base_dir_sead, vignettes), exist_ok=True)  # Create Vignettes folders

    # Generate all permutations of EXCURSION and VIGNETTE
    permutations = list(product(excursion_options, vignette_options))
    
    # Generate files for each permutation
    for perm_index, (excursion, vignette) in enumerate(permutations):
        for run in range(num_runs):
            output_file = os.path.join(cluster_dir, f'run_{perm_index * num_runs + run + 1}.txt')  # Create .txt files
            
            # Set the seed for random number generation based on the seed value
            seed_value = seeds[run % len(seeds)]  # Choose seed for this run
            random.seed(seed_value)  # Set the same seed for generating random values
            
            # Store random values for the current permutation
            random_values = {}
            
            for i, header in enumerate(headers):
                if header_data[i]:  # Ensure there are data points
                    random_values[header] = random.choice(header_data[i])  # Randomly select one value from the list
                else:
                    random_values[header] = 'N/A'  # Placeholder if no valid data

            # Write to output file
            with open(output_file, mode='w') as file:
                unique_id = run + 1  # Unique ID for the run
                file.write(f'$define unique_id {unique_id}\n')  # Write unique_id
                file.write(f'random_seed {seed_value}\n')  # Write the seed value

                # Include original startup file path
                file.write("file_path ../..\n")

                # Include original run file
                file.write("script_variables\n")
                file.write("   string rootPath = \"../\";\n")
                file.write("end_script_variables\n")

                # Include original run file
                file.write("include_once Startup_Germany425.txt\n")

                # Write random values for headers
                for header in headers:
                    file.write(f'$define {header} {random_values[header]}\n')  # Include $define prefix
                
                # Write the excursion and vignette for the current permutation
                file.write(f'$define EXCURSION {excursion}\n')  # Append the excursion
                file.write(f'$define VIGNETTE {vignette}\n')  # Append the vignette


                       ################################
        # # Run DOE
# NOT READY FOR LINUX CLUSTER. DO NOT USE ON CLUSTER YET ################################
    if platform.system() == 'Linux': 
        for iRun in range(num_runs):
            j = 0
            i = 0
            cluster_startup_name = cluster_dir + "\\run_" + str(iRun+1) + ".txt"
            # Creating string to kick off runs 
            runstring = "bsub -q qu -J " + str(seed_value) + " " + linux_afsim_location + " " + cluster_startup_name
            #runstring = afsim_path + " " + cluster_startup_name

            # Run AFSIM if Linux, otherwise just create files (for speed)
            
            os.system(runstring)

            # # Defining run name
            # runname = "Run_%d_%d" %(j,i)

            # # Displaying the scheduling of runs
            print("Scheduling: " + runstring)

            # # Adding 1 to 'i' count
            # i += 1

            # # Adding one to the unique_ID count
            # #unique_id += 1

            # # Adding one to 'j' count
            # j += 1
# NOT READY FOR LINUX CLUSTER. DO NOT USE ON CLUSTER YET ################################

def run_Multi_Run(cluster_dir, num_runs, afsim_location):
    for run_num in range (num_runs):
        multi_Run_Path = cluster_dir + '\\run_' + str(run_num+1) + '.txt'
        subprocess.call([afsim_location, multi_Run_Path])

                
# Example usage

generate_random_files(csv_file, seeds_csv, num_runs, cluster_dir)
if platform.system() == 'Windows':
    run_Multi_Run(cluster_dir,num_runs,afsim_location)