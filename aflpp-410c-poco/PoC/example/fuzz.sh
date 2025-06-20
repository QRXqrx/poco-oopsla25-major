#!/bin/bash

####################################################
# Let's fuzz this small example for several times. #
####################################################

# Global configurations
if [ -z "$AFLPP" ]; then
  echo "Empty AFLPP, set AFLPP first!"
  exit 1
fi

# Parameter checking
if [ $# -lt 5 ]; then
  echo "<CAMPAIGN>: <IN_DIR> <OUTS_DIR> <START_IDX> <END_IDX> <DURATION>"
  exit 1
fi

# Locate afl-fuzz
FUZZER="$AFLPP/afl-fuzz"

# Locate target
EXAMPLE_DIR=$(dirname "$0")
pushd "$EXAMPLE_DIR" || exit 0
  EXAMPLE_DIR=$(pwd)
popd || exit 0
TARGET_PATH="$EXAMPLE_DIR/hello"

# Ck target
if [ ! -e "$TARGET_PATH" ]; then
  echo "Fail to find '$TARGET_PATH', build the example first."
  exit 1
fi

echo "FUZZER=$FUZZER"

# Configure arguments
IN_DIR="$1"
OUTS_DIR=$2
START_IDX="$3"
END_IDX="$4"
DURATION=$5

if [ ! -d "$OUTS_DIR" ]; then
  mkdir -p "$OUTS_DIR"
fi

# Start fuzzing
for idx in $(seq "$START_IDX" "$END_IDX"); do

  # Prepare out directories for fuzzing
  OUT_DIR="$OUTS_DIR/out-$idx"
  if [ -d "$OUT_DIR" ]; then
    rm -rf "$OUT_DIR"
  fi
  mkdir -p "$OUT_DIR"

  # Run fuzzing. Stop at the first crash (Reach abort()).
  AFL_BENCH_UNTIL_CRASH=1 "$FUZZER" -V "$DURATION" -i "$IN_DIR" -o "$OUT_DIR" "$TARGET_PATH"

done
