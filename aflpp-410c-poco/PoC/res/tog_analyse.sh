#!/bin/bash

#将tog_analysis.so应用于指定文件，输出dot

# 检查是否提供了源文件作为参数
if [ $# -ne 1 ]; then
  echo "Usage: $0 <source-file>"
  exit 1
fi

# 设置变量
BC_FILE="$1"
BASENAME=$(basename "$BC_FILE" .c) # 获取文件名（去掉后缀）
PASS_SO="$AFLPP/PoC/res/build/libtog_analysis.so"

echo "BASENAME=$BASENAME"
echo "BC_FILE=$BC_FILE"
echo "PASS_SO=$PASS_SO"

# 3. 使用 SanitizerCoveragePoC 插桩
echo "Instrumenting IR file..."
echo "opt-15 -load-pass-plugin $PASS_SO --passes="tog-analysis" -disable-output "$BC_FILE" "
opt-15 -load-pass-plugin $PASS_SO --passes="tog-analysis" -disable-output "$BC_FILE" 

if [ $? -ne 0 ]; then
  echo "Instrumentation failed."
  exit 1
fi


echo "Process completed"
