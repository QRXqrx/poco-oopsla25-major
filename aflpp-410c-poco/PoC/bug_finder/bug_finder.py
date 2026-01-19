import os
import sys
import subprocess
from subprocess import DEVNULL
tog_set = list()


import os
import sys
from ctypes import *
from ctypes.util import find_library

# Constants from ipc.h and afl-fuzz config.h.
IPC_CREAT           = 0o1000          
IPC_EXCL            = 0o2000          
IPC_NOWAIT          = 0o4000          
IPC_PRIVATE         = 0
IPC_RMID	        = 0	
DEFAULT_PERMISSION  = 0o600

# POC relevant string consants.
TOG_PAT     = 'POC_TOG_'
CMD_DELIM   = '--'
FILEIN_LOC  = '@@'
LOG         = '[LOG]'
LOG_DELIM   = '=================================================='

def load_c_shmat():
    return CDLL(find_library('c')).shmat


def load_c_shmget():
    return CDLL(find_library('c')).shmget


def load_c_shmctl():
    return CDLL(find_library('c')).shmctl


def load_c_shmdt():
    return CDLL(find_library('c')).shmdt


def load_shm(cshmat, cdtype, shmid: int, shmlen: int):
    """
    Attach to shm and return a ptr to this shm. As ctypes treat
    return type as c_int by default, We need to set proper return
    type before invoking a function.

    :param cshmat: the c shmat function to be called
    :param cdtype: the C type of the elements stored in the shm
    :param shmid: id of the shm to load
    :param shmlen: the number of elements assigned for the shm
    :return: a C pointer to the shm
    """
    cshmat.restype = POINTER(cdtype * shmlen)
    return cshmat(shmid, None, 0)


def parse_target_cmd() -> tuple:
    """
    Extract the part of running target binary from sys.argv.
    Also decide the type of input, i.e, use_stdin or use_file.
    """
    if CMD_DELIM not in sys.argv:
        print(f'{os.path.basename(__file__)}: Cannot work without a target binary!')
        print(f'Usage: {os.path.basename(__file__)} ... -- target_bin bin_opts... [@@]')
        exit(0)
    # Split argv and targt_cmd
    _idx = sys.argv.index(CMD_DELIM)
    _argv = sys.argv[1:_idx]
    _target_cmd = sys.argv[_idx+1:]
    # Determine input type, i.e., use_stdin or not.
    _use_stdin = False
    if FILEIN_LOC not in _target_cmd:
        _use_stdin = True
    return _argv, _target_cmd, _use_stdin



def set_env_from_tog(tog_file):
    """Read the tog file and set environment variables."""
    try:
        with open(tog_file, 'r') as f:
            numbers = f.read().strip().split(',')
        print(len(numbers))
        os.environ["POC_DEBUG"]="1"
        os.environ["__POC_SHM_ID"]=str(shm_id)
        for num in numbers:
            # print(num)
            env_var = f'POC_TOG_{num.strip()}'
            os.environ[env_var] = '1'
            tog_set.append(num.strip())
    except Exception as e:
        print(f"Error reading {tog_file}: {e}")
        sys.exit(1)

def run_program(program, input_dir):
    """Enumerate files in input_dir and run the program with each file as an argument."""
    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a valid directory.")
        sys.exit(1)
    
    work_path = os.environ.get("AFLPP")
    # print(LOG,work_path)
    cmin_path = os.path.join(work_path, "afl-cmin")
    output_path = "/tmp/bug_finder"
        # 清空目标目录
    for item in os.listdir(output_path):
        item_path = os.path.join(output_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

    thread_num = "1"
    time_limit = 200
    std = False
    target_cmd = [
        cmin_path,
        "-i", input_dir,  # Input directory
        "-o", output_path,  # Output directory
        # "-t", str(timeout),  # Timeout duration
        # "-m", str(memory),  # Timeout duration
        "-T", thread_num,
        "-t", str(round(time_limit*1000)),
        "--", 
        program, 
        "" if std else "@@",
    ]
    print(f"run : {' '.join(target_cmd)}")
    print(len(os.environ))
    result=subprocess.run(target_cmd, env=os.environ, stdin=sys.stdin)
    if result.returncode !=0 :
        print(f"cmin find something wrong,return code = {result}")
    

    pos = -1
    length = 1
    return_code = 0
    use_stdin=False
    result=set()
    global shm_id
    global shm
    _envs = {"POC_DEBUG" : "1", "__POC_SHM_ID": str(shm_id)}
    for tog in tog_set:
        # print(tog)
        _envs[f'POC_TOG_{tog}'] = "1"
    # global tog_set
    # tog_set = tog_set[::-1]
    while pos + 1 < len(tog_set) :
        # print(f"pos: {pos},length: {length}")
        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)
            return_code = 0
            # print(file_path)
            if use_stdin:
                with open(seed_file, 'rb') as f:
                    process = subprocess.Popen([program], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=os.environ)
            else:
                process = subprocess.Popen([program,file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=os.environ)
            # print(process)
            try:
                stdout, stderr = process.communicate(timeout=time_limit)
            except Exception as e:
                process.kill()
                process.wait()
                process.returncode = -9
                return_code = -9
            # print(process.returncode)
            if return_code == 0 :
                return_code = process.returncode

            if return_code != 0 :
                print("bad case ,please check")
        # for tog in tog_set[pos+1:pos+1+length]:
        #     # print(tog)
        #     _envs[f'POC_TOG_{tog}'] = "1"
        # print(len(result))
        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)
            return_code = 0
            if use_stdin:
                with open(seed_file, 'rb') as f:
                    process = subprocess.Popen([program], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=_envs)
            else:
                process = subprocess.Popen([program,file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=_envs)

            try:
                stdout, stderr = process.communicate(timeout=time_limit)
            except Exception as e:
                print("time out")
                process.kill()
                process.wait()
                return_code = -9
            # print(process.returncode)
            if return_code == 0 :
                return_code = process.returncode

            if return_code < 0 :
                break
        if return_code < 0 :
            print(f"pos = {pos}  leng = {length} total =  {len(tog_set)} return_code = {return_code}")
            # for tog in tog_set[pos+1:pos+1+length]:
            #     del _envs[f'POC_TOG_{tog}'] 
            if length == 1 :
                print(f"find tog : {tog_set[pos+1]}")
                result.add(tog_set[pos+1])
                pos+=1
            else :
                length//=2
        else :
            pos+=length
            length*=2

    print(result)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <tog_file> <program> <input_seed_directory>")
        sys.exit(1)
    
    global shm_id
    global shm
    # Load lots of shm functions from C library.
    c_shmget = load_c_shmget()
    c_shmctl = load_c_shmctl()
    c_shmat = load_c_shmat()
    c_shmdt = load_c_shmdt()

    # Load a shm
    shm_id = c_shmget(IPC_PRIVATE, 1<<16, IPC_CREAT | IPC_EXCL | DEFAULT_PERMISSION)
    shm = load_shm(cshmat=c_shmat, shmid=shm_id, cdtype=c_uint8, shmlen=1<<16)

    tog_file = sys.argv[1]
    program = sys.argv[2]
    input_dir = sys.argv[3]
    
    set_env_from_tog(tog_file)
    run_program(program, input_dir)

