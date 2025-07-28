#!/bin/bash

set -x

TARGET=libtiff_poco_poco_2h FUZZER=aflplusplus ./build.sh
TARGET=libxml2_poco_poco_2h FUZZER=aflplusplus ./build.sh
TARGET=libpng_poco_poco_2h FUZZER=aflplusplus ./build.sh
TARGET=sqlite3_poco_poco_2h FUZZER=aflplusplus ./build.sh
TARGET=lua_poco_poco_2h FUZZER=aflplusplus ./build.sh
TARGET=libtiff_poco_cminplus_2h FUZZER=aflplusplus ./build.sh
TARGET=libxml2_poco_cminplus_2h FUZZER=aflplusplus ./build.sh
TARGET=libpng_poco_cminplus_2h FUZZER=aflplusplus ./build.sh
TARGET=sqlite3_poco_cminplus_2h FUZZER=aflplusplus ./build.sh
TARGET=lua_poco_cminplus_2h FUZZER=aflplusplus ./build.sh
