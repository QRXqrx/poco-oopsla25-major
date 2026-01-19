import os
import shutil
import random
import argparse

def copy_random_files(source_dir, output_dir, num_files):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get all non-hidden files in the source directory
    all_files = [f for f in os.listdir(source_dir) 
                 if os.path.isfile(os.path.join(source_dir, f)) and not f.startswith('.')]
    
    # Get files already existing in the output directory
    existing_files = set(os.listdir(output_dir))
    
    # Filter out files that already exist in the output directory
    available_files = [f for f in all_files if f not in existing_files]
    
    # Randomly select num_files files
    selected_files = random.sample(available_files, min(num_files, len(available_files)))
    
    # Copy the selected files
    for file in selected_files:
        shutil.copy(os.path.join(source_dir, file), os.path.join(output_dir, file))
    
    print(f"Copied {len(selected_files)} files from '{source_dir}' to '{output_dir}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy random non-hidden files from source to output directory.")
    parser.add_argument("source_dir", help="Source directory")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("num_files", type=int, help="Number of files to copy")
    
    args = parser.parse_args()
    copy_random_files(args.source_dir, args.output_dir, args.num_files)
