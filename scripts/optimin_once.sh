#!/bin/bash
# Usage: ./script.sh CORPUS SHOWMAP TARGET
# Parameters:
#   CORPUS      A folder containing seeds.
#   OUT_DIR     Path to showmap output
#   SHOWMAP     Path to afl-showmap
#   TARGET_DIR  Path to the fuzz target dir
#   TARGET      Name of the fuzz target

# Find showmap once
SMONCE_PATH="$(dirname "$0")/showmap_corpus_noC.sh"

if [ -f "${SMONCE_PATH}" ]; then
    echo "Find: ${SMONCE_PATH}"
else
    echo "ERROR: Cannot find showmap_corpus_noC.sh!"
    exit 1
fi

if [ $# -ne 5 ]; then
    echo "Usage: $0 CORPUS OUT_DIR SHOWMAP TARGET_DIR TARGET"
    exit 1
fi

CORPUS="$1"
OUT_DIR="$2"
SHOWMAP="$3"
TARGET_DIR="$4"
TARGET="$5"

start_time=$(date +%s)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Start..."

# Run showmap once.
"$SMONCE_PATH" "$CORPUS/$TARGET" "$OUT_DIR/$TARGET" "$SHOWMAP" "$TARGET_DIR" "$TARGET"

# Run optimin once.
docker run -v "$OUT_DIR/$TARGET":"/tmp/$TARGET" optimin "/tmp/$TARGET" 2> "$OUT_DIR/$TARGET.log"

# Record time
end_time=$(date +%s)
elapsed=$((end_time - start_time))
echo "$elapsed seconds" | tee "$OUT_DIR/$TARGET.time"
