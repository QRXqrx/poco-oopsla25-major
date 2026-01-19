#!/bin/bash

#Apply tog_analysis.so to the specified file and output a DOT file

# Check whether a source file is provided as an argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <source-file>"
  exit 1
fi

# Set a variable
BC_FILE="$1"
BASENAME=$(basename "$BC_FILE" .c) # Get the file name (without the extension)
PASS_SO="$AFLPP/PoC/res/build/libtog_analysis.so"

echo "BASENAME=$BASENAME"
echo "BC_FILE=$BC_FILE"
echo "PASS_SO=$PASS_SO"

# 3. Instrument using SanitizerCoveragePoC
echo "Instrumenting IR file..."
echo "opt-15 -load-pass-plugin $PASS_SO --passes="tog-analysis" -disable-output "$BC_FILE" "
opt-15 -load-pass-plugin $PASS_SO --passes="tog-analysis" -disable-output "$BC_FILE" 

if [ $? -ne 0 ]; then
  echo "Instrumentation failed."
  exit 1
fi


echo "Process completed"
