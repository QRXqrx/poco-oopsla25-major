#!/bin/bash

# Use afl-cmin to minimize the corpus.

# Global configurations
if [ -z "$AFLPP" ]; then
  echo "Empty AFLPP, set AFLPP first!"
  exit 1
fi

# Locate afl-cmin
AFL_CMIN="$AFLPP/afl-cmin"

# Locate example directory
EXAMPLE_DIR=$(dirname "$0")
pushd "$EXAMPLE_DIR" || exit 0
  EXAMPLE_DIR=$(pwd)
popd || exit 0

# Locate example input dir and target; prepare temp corpus dir and result dir
IN_DIR="$EXAMPLE_DIR/in"
TARGET_PATH="$EXAMPLE_DIR/hello"
TEMP_DIR="$EXAMPLE_DIR/temp"
RES_DIR="$EXAMPLE_DIR/afl-cmin"

# Ck target
if [ ! -e "$TARGET_PATH" ]; then
  echo "Fail to find '$TARGET_PATH', build the example first."
  exit 1
fi


# Copy all inputs to temp dir
mkdir "$TEMP_DIR"
cp "$IN_DIR"/in*/* "$TEMP_DIR"

# Conduct afl-cmin
$AFL_CMIN -i "$TEMP_DIR" -o "$RES_DIR" -- "$TARGET_PATH"

# Delete temp dir
rm -rf "$TEMP_DIR"
