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

cd "$TARGET/repo"
./autogen.sh
./configure --disable-shared --enable-ossfuzzers
make -j$(nproc) clean
make -j$(nproc) ossfuzz/sndfile_fuzzer

cp -v ossfuzz/sndfile_fuzzer $OUT/

##poc link command
#~/aflpp-poc-410c/afl-cc $OUT/libsndfile/sndfile_fuzzer.bc -o $OUT/libsndfile/sndfile_fuzzer_poc -lFLAC -lvorbis -lvorbisenc -lopus -logg -lmpg123 -lmp3lame -lm
#./src/.libs/libsndfile.a ./ossfuzz/sndfile_fuzzer.cc ./ossfuzz/.libs/libstandaloneengine.a -I./include