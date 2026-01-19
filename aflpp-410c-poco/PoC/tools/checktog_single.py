import re
import os
import subprocess
import argparse
import sys
from tqdm import tqdm

def validate_poc_tog(poc_file_path, input_dir_path, exec_program_path, output_dir_path):
    # Step 1: Read the POC file and find all strings matching POC_TOG_{}
    with open(poc_file_path, 'r') as file:
        content = file.read()
    poc_togs = re.findall(r'POC_TOG_\d+', content)

    # Initialize sets
    set_ok = set()
    set_crash = set()
    set_tle = set()
    set_wa = set()
    tog_env = dict()

    #debug
    crash_file = set()
    exec_command_file = list()

    # Step 2: Enumerate each POC_TOG_{}
    for poc_tog in tqdm(poc_togs, desc="Processing POC_TOGs"):
        #Track whether the TOG causes a crash or TLE, and whether the output is correct
        poc_valid = True
        poc_right = True

        # Nested loop over each input file in the input directory
        for input_file in tqdm(os.listdir(input_dir_path), desc=f"Testing {poc_tog}", leave=False):
            input_file_path = os.path.join(input_dir_path, input_file)
            #print('now we are going to run {0} {1}'.format(exec_program_path,input_file_path))
            # Construct the command line and execute the program
            process = subprocess.Popen([exec_program_path, input_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

            try:
                #The selected inputs are small; a 10s timeout is sufficient to detect unreasonable instrumentation logic
                result_without_tog = process.communicate(timeout=10)
            except Exception as e:
                #heoretically impossible: error occurs without any TOG set
                #print(f'fatal error:impossible stuation : crash in {input_file_path}')
                #sys.exit(1)
                #let's just ignore first
                crash_file.add(input_file_path)
                continue

            # Check for Segmentation fault
            if process.returncode == -11:
                #Theoretically impossible: error occurs without any TOG set
                #print(f'fatal error:impossible stuation : crash in {input_file_path}')
                #sys.exit(1)
                #let's just ignore first
                crash_file.add(input_file_path)
                continue

            #Set the current TOG to 1
            tog_env[poc_tog] = '1'

            process = subprocess.Popen([exec_program_path, input_file_path],
                                        env=tog_env,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            try:
                #10s timeout to catch unreasonable instrumentation behavior
                result_with_tog = process.communicate(timeout=10)
            except Exception as e:
                process.kill()
                set_tle.add(poc_tog)
                poc_valid=False
                exec_command_file.append(f'tle: {poc_tog}=1 {exec_program_path} {input_file_path}')
                break

            # Check for Segmentation fault
            if process.returncode == 139:
                set_crash.add(poc_tog)
                poc_valid=False
                exec_command_file.append(f'crash: {poc_tog}=1 {exec_program_path} {input_file_path}')
                break

            if result_with_tog != result_without_tog:
                #print(f'expected : \n{result_without_tog}\n read: \n{result_with_tog}\n')
                poc_right=False
                set_wa.add(poc_tog)
                exec_command_file.append(f'wa: {poc_tog}=1 {exec_program_path} {input_file_path}')
                break       

        if poc_valid and poc_right:
            set_ok.add(poc_tog)
        del(tog_env[poc_tog])

        print(f'set_ok:{set_ok}')
        print(f'set_crash:{set_crash}')
        print(f'set_tle:{set_tle}')
        print(f'set_wa:{set_wa}')
        print(f'crash_file:{crash_file}')
        print(f'tog_env:{tog_env}')


    # Step 3: Output the sets to the specified directory
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

    # Check if the POC file path exists
    if not os.path.isfile(args.poc_file_path):
        raise FileNotFoundError(f"POC文件路径不存在: {args.poc_file_path}")

    #  Check if the input directory exists
    if not os.path.isdir(args.input_dir_path):
        raise NotADirectoryError(f"输入目录路径不存在: {args.input_dir_path}")

    # Check if the executable program exists and is executable
    if not os.path.isfile(args.exec_program_path) or not os.access(args.exec_program_path, os.X_OK):
        raise FileNotFoundError(f"可执行程序路径不存在或不可执行: {args.exec_program_path}")

    # Check if the output directory exists, create it if not
    if not os.path.exists(args.output_dir_path):
        os.makedirs(args.output_dir_path)


    validate_poc_tog(args.poc_file_path, args.input_dir_path, args.exec_program_path, args.output_dir_path)
