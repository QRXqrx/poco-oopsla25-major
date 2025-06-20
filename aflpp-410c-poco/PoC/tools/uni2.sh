#!/bin/bash

# 检查参数数量
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 output_dir input_dir"
  exit 1
fi

# 读取输出目录和输入目录
output_dir=$1
input_dir=$2

# 检查输出目录是否存在，否则创建
if [ ! -d "$output_dir" ]; then
  mkdir -p "$output_dir"
fi

# 初始化一个空的文件集合
declare -A files_set

# 递归地收集所有文件到集合中
while IFS= read -r -d '' file; do
  base_file=$(basename "$file")
  files_set["$base_file"]="$file"
done < <(find "$input_dir" -type f -print0)

# 将集合中的文件复制到输出目录
for file in "${!files_set[@]}"; do
  cp "${files_set[$file]}" "$output_dir/"
done

echo "All files from $input_dir have been copied to $output_dir"