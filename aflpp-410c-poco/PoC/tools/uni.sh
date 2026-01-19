#!/bin/bash

# Check the number of arguments
if [ "$#" -lt 3 ]; then
  echo "Usage: $0 output_dir dir1 dir2 [dir3 ... dirN]"
  exit 1
fi

# Read the output directory
output_dir=$1
shift

# Check if the output directory exists; if not, create it
if [ ! -d "$output_dir" ]; then
  mkdir -p "$output_dir"
fi

# Initialize an empty associative array to store files
declare -A files_set

# Iterate over all input directories and collect all files into the array
for dir in "$@"; do
  for file in "$dir"/*; do
    if [ -f "$file" ]; then
      base_file=$(basename "$file")
      files_set["$base_file"]="$file"
    fi
  done
done

#  Copy all files from the array to the output directory
for file in "${!files_set[@]}"; do
  cp "${files_set[$file]}" "$output_dir/"
done

echo "Files copied to $output_dir"