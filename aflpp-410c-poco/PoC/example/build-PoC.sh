#!/bin/bash

# Build the example with afl-cc.

# Global configurations
if [ -z "$AFLPP" ]; then
  echo "Empty AFLPP, set AFLPP first!"
  exit 1
fi

CC="$AFLPP/afl-cc"

echo "CC=$CC"

AFL_LLVM_INSTRUMENT=PoC $CC -o checkpass checkpass.c
