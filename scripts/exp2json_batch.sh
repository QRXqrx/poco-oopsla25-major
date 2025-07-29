#!/bin/bash
# exp2json.py in batch
# Usage: ./script.sh <TOOL_PATH> <TARGET_DIR>


if [ $# -ne 2 ]; then
    echo -e "\033[31m[ERROR] Usage: $0 TOOL_PATH TARGET_DIR\033[0m" 
    exit 1
fi

TOOL_PATH="$1"
TARGET_DIR="$2"

if [ ! -f "$TOOL_PATH" ]; then
    echo -e "\033[31m[ERROR] Invalid tool path: $TOOL_PATH\033[0m"
    exit 2
fi

if [ ! -d "$TARGET_DIR" ]; then
    echo -e "\033[31m[ERROR] Invalid target dir: $TARGET_DIR\033[0m"
    exit 3
fi


for subdir in "$TARGET_DIR"/*/; do
    subdir=${subdir%/}
    
    if [ -d "$subdir" ]; then

        output_json="$subdir/bugs.json"

        # Check tar mark
        if [ -f "$output_json" ]; then
            echo "Find $output_json, skip" 
            continue
        fi

        echo "Doing: $TOOL_PATH $subdir $output_json ..."
        if ! "$TOOL_PATH" "$subdir" "$output_json"; then
            echo -e "\033[33m[WARNING] Failed: $subdir\033[0m"
        else
            echo -e "\033[32m[SUCCESS] Finished: $subdir\033[0m"
        fi
        
    fi
done

echo "====================================="
echo "We are done here! :-)"
echo "====================================="
exit 0
