#!/bin/bash

# 检查参数数量
if [ "$#" -lt 3 ]; then
  echo "Usage: $0 output_dir dir1 dir2 [dir3 ... dirN]"
  exit 1
fi

# 读取输出目录
output_dir=$1
shift

# 检查输出目录是否存在，否则创建
if [ ! -d "$output_dir" ]; then
  mkdir -p "$output_dir"
fi

# 初始化一个空的文件集合
declare -A files_set

# 迭代所有输入目录，收集所有文件到集合中
for dir in "$@"; do
  for file in "$dir"/*; do
    if [ -f "$file" ]; then
      base_file=$(basename "$file")
      files_set["$base_file"]="$file"
    fi
  done
done

# 将集合中的文件复制到输出目录
for file in "${!files_set[@]}"; do
  cp "${files_set[$file]}" "$output_dir/"
done

echo "Files copied to $output_dir"