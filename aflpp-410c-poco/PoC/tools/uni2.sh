#!/bin/bash

#  Check the number of arguments
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 output_dir input_dir"
  exit 1
fi

# Read the output directory and input directory
output_dir=$1
input_dir=$2

# Check if the output directory exists; if not, create it
if [ ! -d "$output_dir" ]; then
  mkdir -p "$output_dir"
fi

# Initialize an empty associative array to store files
declare -A files_set

# Recursively collect all files into the array
while IFS= read -r -d '' file; do
  base_file=$(basename "$file")
  files_set["$base_file"]="$file"
done < <(find "$input_dir" -type f -print0)

# Copy all files from the array to the output directory
for file in "${!files_set[@]}"; do
  cp "${files_set[$file]}" "$output_dir/"
done

echo "All files from $input_dir have been copied to $output_dir"