#!/bin/bash

#Apply SanitizerCoveragePoC.so to the specified file and output a human-readable IR file

# Check whether a source file is provided as an argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <source-file>"
  exit 1
fi

# Set variables
SOURCE_FILE="$1"
BASENAME=$(basename "$SOURCE_FILE" .c) # Get the file name without the extension
BC_FILE="${BASENAME}.bc"
INSTR_BC_FILE="${BASENAME}.instr.bc"
LL_FILE="${BASENAME}.ll"
PASS_SO="$AFLPP/SanitizerCoveragePoC.so"

echo "SOURCE_FILE=$SOURCE_FILE"
echo "BASENAME=$BASENAME"
echo "BC_FILE=$BC_FILE"
echo "INSTR_BC_FILE=$INSTR_BC_FILE"
echo "LL_FILE=$LL_FILE"
echo "PASS_SO=$PASS_SO"

# 1. Compile the source file using gclang
echo "Compiling $SOURCE_FILE with gclang..."
gclang -c "$SOURCE_FILE" -o "$BASENAME"
if [ $? -ne 0 ]; then
  echo "gclang compilation failed."
  exit 1
fi

# 2. Use get-bc to generate the intermediate representation (IR) file
echo "Generating IR file..."
get-bc "$BASENAME" 
if [ $? -ne 0 ]; then
  echo "Failed to generate IR file."
  exit 1
fi

# 3. Instrument the IR using SanitizerCoveragePoC
echo "Instrumenting IR file..."
echo "opt-14 -load-pass-plugin $PASS_SO --passes="SanitizerCoveragePoc"  "$BC_FILE" -o "$INSTR_BC_FILE""
opt-14 -load-pass-plugin $PASS_SO --passes="SanitizerCoveragePoc"  "$BC_FILE" -o "$INSTR_BC_FILE"
if [ $? -ne 0 ]; then
  echo "Instrumentation failed."
  exit 1
fi

# 4. Convert the instrumented IR file to a human-readable LL file
echo "Generating readable LL file..."
llvm-dis-14 "$INSTR_BC_FILE" -o "$LL_FILE"
if [ $? -ne 0 ]; then
  echo "Failed to generate LL file."
  exit 1
fi

echo "Process completed. The instrumented LL file is: $LL_FILE"
