#!/bin/bash

#将SanitizerCoveragePoC.so应用于指定文件，输出可读的ir文件

# 检查是否提供了源文件作为参数
if [ $# -ne 1 ]; then
  echo "Usage: $0 <source-file>"
  exit 1
fi

# 设置变量
SOURCE_FILE="$1"
BASENAME=$(basename "$SOURCE_FILE" .c) # 获取文件名（去掉后缀）
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

# 1. 使用 gclang 编译源文件
echo "Compiling $SOURCE_FILE with gclang..."
gclang -c "$SOURCE_FILE" -o "$BASENAME"
if [ $? -ne 0 ]; then
  echo "gclang compilation failed."
  exit 1
fi

# 2. 使用 get-bc 获取中间表示 (IR) 文件
echo "Generating IR file..."
get-bc "$BASENAME" 
if [ $? -ne 0 ]; then
  echo "Failed to generate IR file."
  exit 1
fi

# 3. 使用 SanitizerCoveragePoC 插桩
echo "Instrumenting IR file..."
echo "opt-14 -load-pass-plugin $PASS_SO --passes="SanitizerCoveragePoc"  "$BC_FILE" -o "$INSTR_BC_FILE""
opt-14 -load-pass-plugin $PASS_SO --passes="SanitizerCoveragePoc"  "$BC_FILE" -o "$INSTR_BC_FILE"
if [ $? -ne 0 ]; then
  echo "Instrumentation failed."
  exit 1
fi

# 4. 将插桩后的 IR 文件转换为可读的 LL 文件
echo "Generating readable LL file..."
llvm-dis-14 "$INSTR_BC_FILE" -o "$LL_FILE"
if [ $? -ne 0 ]; then
  echo "Failed to generate LL file."
  exit 1
fi

echo "Process completed. The instrumented LL file is: $LL_FILE"
