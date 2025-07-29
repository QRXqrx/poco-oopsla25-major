#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <ROOT_PATH>"
    exit 1
fi

ROOT_PATH="$1"

# Find ball.tar
find "$ROOT_PATH" -name 'ball.tar' -print0 | while IFS= read -r -d $'\0' tar_file; do
    # Locate the dir of ball.tar
    dir_path=$(dirname "$tar_file")
    
    echo "Check: $dir_path"
    
    # Check tar mark
    if [ -f "${dir_path}/ball-untared" ]; then
        echo "Find ball-untared, skip" 
        continue
    fi
    
    echo "Untar: $tar_file"
    if tar xf "$tar_file" -C "$dir_path" ; then
        echo "Success: $dir_path"
        touch "${dir_path}/ball-untared" 2>/dev/null
    else
        echo "Failed: $tar_file" >&2
        exit 2
    fi
done

echo "Finished :-)"
