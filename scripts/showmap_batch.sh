#!/bin/bash
# Usage: ./script.sh FINDINGS SHOWMAP TARGET
# Parameters:
#   FINDINGS    Magma findings
#   OUT_DIR     Path to showmap output
#   SHOWMAP     Path to afl-showmap
#   TARGET_DIR  Path to the fuzz target dir
#   TARGET      Name of the fuzz target

if [ $# -ne 5 ]; then
    echo "Usage: $0 FINDINGS OUT_DIR SHOWMAP TARGET_DIR TARGET"
    exit 1
fi

FINDINGS="$1"
OUT_DIR="$2"
SHOWMAP="$3"
TARGET_DIR="$4"
TARGET="$5"

if [ ! -d "$FINDINGS" ]; then
    echo "Invalid dir: $FINDINGS"
    exit 2
fi

if [ ! -d "$TARGET_DIR" ]; then
    echo "Invalid dir: $TARGET_DIR"
    exit 3
fi

if [ ! -d "$OUT_DIR" ]; then
    mkdir -p "$OUT_DIR"
    echo "Create: $OUT_DIR"
fi

total=0
success=0
failures=0

echo "========================================"
echo "Start processing: $FINDINGS"
echo "Start time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

# CMD for targets.
declare -A CMD_MAP
CMD_MAP["libpng_read_fuzzer"]=""
CMD_MAP["sndfile_fuzzer"]="@@"
CMD_MAP["xmllint"]="@@"
CMD_MAP["libxml2_xml_read_memory_fuzzer"]=""
CMD_MAP["tiff_read_rpga"]=""
CMD_MAP["tiffcp"]="-M @@ /tmp/tiffcp.out"
CMD_MAP["sqlite3_fuzz"]=""
CMD_MAP["lua"]="@@"

CMD="${CMD_MAP[$TARGET]}"
echo "CMD=$CMD"

export AFL_MAP_SIZE=2097152

TARGET="$TARGET_DIR/$TARGET"_poc
while IFS= read -r -d '' subdir; do
    ((total++))
    idx=$(basename "$subdir")
    output_file="$OUT_DIR/showmap-${idx}.out"
        
    IN_DIR="$subdir/findings/default/queue"
    echo "▶ Processing $IN_DIR"

    echo "$SHOWMAP -C -i $IN_DIR -o $output_file -- $TARGET $CMD"

    # if "$SHOWMAP" -C -i "$IN_DIR" -o "$output_file" -- "$TARGET" "$CMD"; then
    if $SHOWMAP -C -i $IN_DIR -o $output_file -- $TARGET $CMD; then
        echo "✓ SUCCESS: $output_file"
        ((success++))
    else
        echo "✗ FAILED: $IN_DIR!"
        ((failures++))
    fi

    # $SHOWMAP -C -i $IN_DIR -o $output_file -- $TARGET @@
    # "$SHOWMAP" -C -i "$IN_DIR" -o "$output_file" -- "$TARGET" ""
    
    echo "----------------------------------------"
done < <(find "$FINDINGS" -mindepth 1 -maxdepth 1 -type d -print0)

echo "Complete!"
echo "Total: $total"
echo "Success: $success"
echo "Failures: $failures"

if [ $failures -gt 0 ]; then
    exit 4
else
    exit 0
fi