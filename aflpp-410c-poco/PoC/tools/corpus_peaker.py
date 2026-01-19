import os
import shutil
import random
import argparse

def select_random_files(input_dir, output_dir, num_files):
    if not os.path.exists(input_dir) or not os.path.isdir(input_dir):
        print("Input directory does not exist or is not a directory")
        return
    
    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    if len(files) < num_files:
        print("The number of files in the input directory is less than the specified amount")
        return
    
    selected_files = random.sample(files, num_files)
    os.makedirs(output_dir, exist_ok=True)
    
    for file in selected_files:
        shutil.copy(os.path.join(input_dir, file), os.path.join(output_dir, file))
    
    print(f"Randomly selected {num_files} files have been copied to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Randomly select a specified number of files from the input directory to the output directory")
    parser.add_argument("input_dir", type=str, help="Path to the input directory")
    parser.add_argument("output_dir", type=str, help="Path to the output directory")
    parser.add_argument("num_files", type=int, help="Number of files to select")
    
    args = parser.parse_args()
    select_random_files(args.input_dir, args.output_dir, args.num_files)