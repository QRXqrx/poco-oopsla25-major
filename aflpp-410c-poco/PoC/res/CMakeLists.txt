cmake_minimum_required(VERSION 3.10)
project(tog_analysis)

set(CMAKE_CXX_STANDARD 14)

set(LLVM_PATH /usr/lib/llvm-15)
set(CMAKE_LINKER /usr/bin/llvm-link-15)

include_directories(${LLVM_PATH}/include)
include_directories(./)

set(CMAKE_CXX_FLAGS "-g")

add_library(tog_analysis MODULE ./tog_analysis.cc)

set_target_properties(tog_analysis PROPERTIES
        COMPILE_FLAGS "-fno-rtti"
        )

target_link_libraries(tog_analysis ${LLVM_PATH}/lib/libLLVM-15.so) 

SET(LIBRARY_OUTPUT_PATH ${PROJECT_SOURCE_DIR}/build)