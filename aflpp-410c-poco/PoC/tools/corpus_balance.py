import os
import shutil
import random
import argparse

def copy_random_files(source_dir, output_dir, num_files):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 获取源目录中所有非隐藏文件
    all_files = [f for f in os.listdir(source_dir) 
                 if os.path.isfile(os.path.join(source_dir, f)) and not f.startswith('.')]
    
    # 获取输出目录已有的文件
    existing_files = set(os.listdir(output_dir))
    
    # 过滤出输出目录中不存在的文件
    available_files = [f for f in all_files if f not in existing_files]
    
    # 随机选择 num_files 个文件
    selected_files = random.sample(available_files, min(num_files, len(available_files)))
    
    # 复制文件
    for file in selected_files:
        shutil.copy(os.path.join(source_dir, file), os.path.join(output_dir, file))
    
    print(f"Copied {len(selected_files)} files from '{source_dir}' to '{output_dir}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy random non-hidden files from source to output directory.")
    parser.add_argument("source_dir", help="Source directory")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("num_files", type=int, help="Number of files to copy")
    
    args = parser.parse_args()
    copy_random_files(args.source_dir, args.output_dir, args.num_files)
