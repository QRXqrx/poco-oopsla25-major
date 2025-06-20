import os
import shutil
import random
import argparse

def select_random_files(input_dir, output_dir, num_files):
    if not os.path.exists(input_dir) or not os.path.isdir(input_dir):
        print("输入目录不存在或不是一个目录")
        return
    
    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    if len(files) < num_files:
        print("输入目录中的文件数量少于指定的数量")
        return
    
    selected_files = random.sample(files, num_files)
    os.makedirs(output_dir, exist_ok=True)
    
    for file in selected_files:
        shutil.copy(os.path.join(input_dir, file), os.path.join(output_dir, file))
    
    print(f"已随机选取 {num_files} 个文件复制到 {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从输入目录随机选取指定数量的文件到输出目录")
    parser.add_argument("input_dir", type=str, help="输入目录路径")
    parser.add_argument("output_dir", type=str, help="输出目录路径")
    parser.add_argument("num_files", type=int, help="要选择的文件数量")
    
    args = parser.parse_args()
    select_random_files(args.input_dir, args.output_dir, args.num_files)
