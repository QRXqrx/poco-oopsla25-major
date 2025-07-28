#!/bin/bash
set -e

##
# Pre-requirements:
# - env TARGET: path to target work dir
# - env OUT: path to directory where artifacts are stored
# - env CC, CXX, FLAGS, LIBS, etc...
##

if [ ! -d "$TARGET/repo" ]; then
    echo "fetch.sh must be executed first."
    exit 1
fi

# build lua library
cd "$TARGET/repo"
make -j$(nproc) clean
make -j$(nproc) liblua.a

cp liblua.a "$OUT/"

# build driver
make -j$(nproc) lua
cp lua "$OUT/"

# ~/aflpp-poc-410c/afl-cc -o $OUT/lua_poc   -Wfatal-errors -Wextra -Wshadow -Wsign-compare -Wundef -Wwrite-strings -Wredundant-decls -Wdisabled-optimization -Wdouble-promotion  -Wdeclaration-after-statement  -Wmissing-prototypes -Wnested-externs -Wstrict-prototypes -Wc++-compat -Wold-style-definition   -Wlogical-op -Wno-aggressive-loop-optimizations  -Wl,-E $OUT/lua.bc $OUT/liblua.a -lm -ldl -lreadline