#!/bin/bash

# 将tog_analysis.so应用于指定文件，输出dot

# Parameter checks
if [ $# -ne 1 ]; then
  echo "Usage: $0 <source-file>"
  exit 1
fi

# Setting variables
BC_FILE="$1"
BASENAME=$(basename "$BC_FILE" .c) 
PASS_SO="$AFLPP/PoC/res/build/libtog_analysis.so" # Locate the pass

echo "BASENAME=$BASENAME"
echo "BC_FILE=$BC_FILE"
echo "PASS_SO=$PASS_SO"

# Doing compile-time intrumentation using libtog_analysis.so.
echo "Instrumenting IR file..."
echo "opt-15 -load-pass-plugin $PASS_SO --passes="tog-analysis" -disable-output "$BC_FILE" "
opt-15 -load-pass-plugin $PASS_SO --passes="tog-analysis" -disable-output "$BC_FILE" 

if [ $? -ne 0 ]; then
  echo "Instrumentation failed."
  exit 1
fi


echo "Process completed"
