#!/bin/bash

# 检查是否提供了目录参数
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# 获取指定的目录
DIR="$1"

# 检查目录是否存在
if [ ! -d "$DIR" ]; then
  echo "Error: Directory $DIR does not exist."
  exit 1
fi

# 遍历指定目录下的每个一级子目录
for subdir in "$DIR"/*; do
  if [ -d "$subdir" ]; then
    echo "Processing $subdir"
    # 切换到子目录
    cd "$subdir" || continue
    # 检查 tar 文件是否存在
    if [ -f "ball.tar" ]; then
      # 解压 tar 文件
      tar -xvf ball.tar
    else
      echo "Warning: ball.tar not found in $subdir"
    fi
    # 返回上一级目录
    cd - > /dev/null || exit
  fi
done

echo "Done."