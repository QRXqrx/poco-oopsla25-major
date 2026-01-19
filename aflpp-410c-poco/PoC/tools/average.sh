#!/bin/bash

# Ensure that a directory argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

DIR="$1"
SUM=0
COUNT=0

# Iterate over all numbered folders in the directory
for folder in "$DIR"/*; do
    if [ -d "$folder" ]; then
        # Enter the folder
        cd "$folder" || continue

        # Extract ball.tar
        if [ -f "ball.tar" ]; then
            tar -xf ball.tar
        else
            echo "Warning: $folder/ball.tar not found, skipping..."
            cd - > /dev/null
            continue
        fi

        # Locate the findings/default/plot_data file
        PLOT_DATA="findings/default/plot_data"
        if [ -f "$PLOT_DATA" ]; then
            # Get the last line
            LAST_LINE=$(tail -n 1 "$PLOT_DATA")
            # Extract the last number (remove commas and keep only the numeric value)
            LAST_NUM=$(echo "$LAST_LINE" | awk -F '[ ,%]+' '{print $(NF)}')

            # Ensure it is a number
            if [[ "$LAST_NUM" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
                SUM=$(echo "$SUM + $LAST_NUM" | bc -l)
                COUNT=$((COUNT + 1))
            else
                echo "Warning: No valid number found in $PLOT_DATA"
            fi
        else
            echo "Warning: $folder/$PLOT_DATA not found"
        fi

        # Return to the original directory
        cd - > /dev/null
    fi
done

# Calculate the average
if [ "$COUNT" -gt 0 ]; then
    AVG=$(echo "$SUM / $COUNT" | bc -l)
    echo "Average: $AVG"
else
    echo "No valid numbers found."
fi
