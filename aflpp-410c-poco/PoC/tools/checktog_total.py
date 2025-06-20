import re
import os
import subprocess
import argparse
import sys
from tqdm import tqdm

def validate_poc_tog(poc_file_path, input_dir_path, exec_program_path, output_dir_path):
    # Step 1: 读取POC文件，并找到所有形如POC_TOG_{}的字符串
    with open(poc_file_path, 'r') as file:
        content = file.read()
    poc_togs = re.findall(r'POC_TOG_\d+', content)

    # 初始化集合
    set_ok = set()
    set_crash = set()
    set_tle = set()
    set_wa = set()
    tog_env = dict()

    #debug
    crash_file = set()
    exec_command_file = list()

    # Step 2: 枚举每个POC_TOG_{}
    for poc_tog in tqdm(poc_togs, desc="Processing POC_TOGs"):
        #记录tog是否crash或者tle，以及是否输出结果正确
        poc_valid = True
        poc_right = True

        # 二重枚举每个输入集路径下的输入文件
        for input_file in tqdm(os.listdir(input_dir_path), desc=f"Testing {poc_tog}", leave=False):
            input_file_path = os.path.join(input_dir_path, input_file)
            #print('now we are going to run {0} {1}'.format(exec_program_path,input_file_path))
            # 构建命令行参数，执行程序
            process = subprocess.Popen([exec_program_path, input_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

            try:
                #选择的都是小数据，10s基本上就是出现了不合理的插桩逻辑
                result_without_tog = process.communicate(timeout=10)
            except Exception as e:
                #理论上不可能的情况：没有设置任何tog的情况下出现错误
                #print(f'fatal error:impossible stuation : crash in {input_file_path}')
                #sys.exit(1)
                #let's just ignore first
                crash_file.add(input_file_path)
                continue

            # 检查是否发生Segmentation fault
            if process.returncode != 0:
                #理论上不可能的情况：没有设置任何tog的情况下出现错误
                #print(f'fatal error:impossible stuation : crash in {input_file_path}')
                #sys.exit(1)
                #let's just ignore first
                crash_file.add(input_file_path)
                continue

            #将该TOG设置为1
            tog_env[poc_tog] = '1'

            process = subprocess.Popen([exec_program_path, input_file_path],
                                        env=tog_env,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            try:
                #选择的都是小数据，10s基本上就是出现了不合理的插桩逻辑
                result_with_tog = process.communicate(timeout=10)
            except Exception as e:
                process.kill()
                set_tle.add(poc_tog)
                poc_valid=False
                exec_command_file.append(f'tle: {poc_tog}=1 {exec_program_path} {input_file_path}')
                # break

            # 检查是否发生Segmentation fault
            if process.returncode != 0:
                set_crash.add(poc_tog)
                poc_valid=False
                exec_command_file.append(f'crash: {poc_tog}=1 {exec_program_path} {input_file_path}')
                # break

            if result_with_tog != result_without_tog:
                print(f'expected : \n{result_without_tog}\n read: \n{result_with_tog}\n')
                poc_right=False
                set_wa.add(poc_tog)
                exec_command_file.append(f'wa: {poc_tog}=1 {exec_program_path} {input_file_path}')
                # break       

        if poc_valid and poc_right:
            set_ok.add(poc_tog)
        else:
            del(tog_env[poc_tog])

        print(f'set_ok:{set_ok}')
        print(f'set_crash:{set_crash}')
        print(f'set_tle:{set_tle}')
        print(f'set_wa:{set_wa}')
        print(f'crash_file:{crash_file}')
        #print(f'tog_env:{tog_env}')


    # Step 3: 输出集合到指定路径
    with open(os.path.join(output_dir_path, 'ok.txt'), 'w') as ok_file:
        for poc in set_ok:
            ok_file.write(f"export {poc}=1\n")

    with open(os.path.join(output_dir_path, 'wa.txt'), 'w') as wa_file:
        for poc in set_wa:
            wa_file.write(f"export {poc}=1\n")

    with open(os.path.join(output_dir_path, 'tle.txt'), 'w') as tle_file:
        for poc in set_tle:
            tle_file.write(f"export {poc}=1\n")

    with open(os.path.join(output_dir_path, 'crash.txt'), 'w') as crash_file:
        for poc in set_crash:
            crash_file.write(f"export {poc}=1\n")

    with open(os.path.join(output_dir_path, 'command.txt'), 'w') as command_file:
        for poc in exec_command_file:
            command_file.write(f"{poc}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate POC_TOG entries in a file using a set of inputs and a program.")
    parser.add_argument('poc_file_path', help="Path to the POC file to be read")
    parser.add_argument('input_dir_path', help="Path to the directory containing input files")
    parser.add_argument('exec_program_path', help="Path to the executable program")
    parser.add_argument('output_dir_path', help="Path to the directory where output files will be saved")

    args = parser.parse_args()

    # 检查POC文件路径是否存在
    if not os.path.isfile(args.poc_file_path):
        raise FileNotFoundError(f"POC文件路径不存在: {args.poc_file_path}")

    # 检查输入目录路径是否存在
    if not os.path.isdir(args.input_dir_path):
        raise NotADirectoryError(f"输入目录路径不存在: {args.input_dir_path}")

    # 检查可执行程序路径是否存在且为可执行文件
    if not os.path.isfile(args.exec_program_path) or not os.access(args.exec_program_path, os.X_OK):
        raise FileNotFoundError(f"可执行程序路径不存在或不可执行: {args.exec_program_path}")

    # 检查输出目录路径是否存在，若不存在则创建
    if not os.path.exists(args.output_dir_path):
        os.makedirs(args.output_dir_path)


    validate_poc_tog(args.poc_file_path, args.input_dir_path, args.exec_program_path, args.output_dir_path)
