#!/bin/bash

# Check if a directory argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Get the specified directory
DIR="$1"

# Check if the directory exists
if [ ! -d "$DIR" ]; then
  echo "Error: Directory $DIR does not exist."
  exit 1
fi

# Iterate over each first-level subdirectory in the specified directory
for subdir in "$DIR"/*; do
  if [ -d "$subdir" ]; then
    echo "Processing $subdir"
    # Change to the subdirectory
    cd "$subdir" || continue
    # Check if the tar file exists
    if [ -f "ball.tar" ]; then
      # Extract the tar file
      tar -xvf ball.tar
    else
      echo "Warning: ball.tar not found in $subdir"
    fi
    # Return to the previous directory
    cd - > /dev/null || exit
  fi
done

echo "Done."
