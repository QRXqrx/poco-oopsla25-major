"""
To run given test inputs (seeds) and collect the toggles
that has been passed. 
"""

import os
import copy
import resource
import shutil
import argparse
import subprocess
import datetime
import numpy as np
import pandas as pd
import networkx as nx
import pydot
import re
import signal
import time
import random

from collections import deque
from tqdm import tqdm
from subprocess import DEVNULL
from poccshm import *


# Default TOG_MAP_SIZE = 1 << 16, so the default number should -2
DEFAULT_TOG_NUM = (1 << 16) 
result = None
tmp_path = ""
revoke_seed_path = ""
min_time_limit = 5.0
max_time_limit = 20.0
r1 = 0.1
r2 = 0.01
time_limit = max_time_limit
crash_detected_time_limit = max_time_limit
cmin_time_limit = max_time_limit
node_id_map = {}
cmin_path = ""


def disable_core(): #Disable core dumps
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def run_target_poc(target_args: list, shmid: int, open_tog_set: set,
                   be_quiet: bool =False):
    _envs = {"POC_DEBUG" : "1", "__POC_SHM_ID": str(shmid)}
    global result
    for _ in open_tog_set:
        _envs[f'{TOG_PAT}{_}'] = "1"
    if be_quiet:
        result=subprocess.run(target_args, env=_envs, stdin=sys.stdin, stdout=DEVNULL, stderr=DEVNULL)
    else:
        print(LOG, '+++++++++++++++ Program Outputs +++++++++++++++ ')
        result=subprocess.run(target_args, env=_envs, stdin=sys.stdin)
        print(LOG, '+++++++++++++++++++++++++++++++++++++++++++++++ ')

    


def execute_cases_and_update_map(
        open_tog_set: set,
        cmd: list, 
        shmid: int, togshm,
        mapsize: int = DEFAULT_TOG_NUM,
        be_quiet: bool = False) -> np.array:
    """ 
    Execute every test cases inside the given casedir and return 
    the resultant toggle map.
    """
    # Prepare 
    _tog_set = set()
    
    # use_file, replace @@ with the path to the file.            
    # _idx = _cmd.index(FILEIN_LOC)
    # _cmd[_idx] = casedir

    
    run_target_poc(cmd, shmid=shmid, open_tog_set=open_tog_set,be_quiet=be_quiet)  

    # Update global tog map.
    for _i in range(1, mapsize):
        if togshm[0][_i]:
            _tog_set.add(_i)
            # Clean shm
            togshm[0][_i] = 0

    return _tog_set



def build_arg_parser() -> argparse.ArgumentParser:
    """
    Build command line argument parser.
    :return: Arg parser instance.
    """
    _p = argparse.ArgumentParser()
    _p.add_argument('--in_dir', '-i', required=True, type=str,
                    help='seed path to start first cmin')
    _p.add_argument('--out_dir', '-o', required=True, type=str,
                    help='Directory path to store the cmin result.')
    _p.add_argument('--graph_dir', '-g', required=True, type=str,
                    help='graph path to parse coverage guards.')
    _p.add_argument('--exec', '-e', required=True, type=str,
                    help='exec file path to cmin')
    _p.add_argument('--num_toggle', '-n', required=False, type=int, default=DEFAULT_TOG_NUM,
                    help='Directory to output toggle analysis results.')
    _p.add_argument('--num_tog_dump', '-N', required=False, type=str, default=None,
                    help='Dump file recording toggle number.')
    _p.add_argument('--quiet', '-q', required=False, action='store_true',
                    help='Whether hide target output.')
    _p.add_argument('--task', '-t', required=False, type=str,default='1',
                    help='how many parallel tasks to run (default: 1, all=nproc)')
    _p.add_argument('--TimeOut', '-T', required=False, type=int,default=5*24*60*60, #default = 5days
                help='time limit to poff (default: 5 days)')
    return _p

def count_files_in_directory(directory):
    # Get all files and folders in the directory
    entries = os.listdir(directory)
    
    # Filter out hidden files
    files = [entry for entry in entries if not entry.startswith(".") and os.path.isfile(os.path.join(directory, entry))]
    
    # Return the number of files
    return len(files) 


def revoke_seeds_finder(open_tog_set: list ,seed_dir: str,exec_file: str,exec_parameter: list,shmid: str):
    # Get all files in seed_dir
    seed_files = [os.path.join(seed_dir, f) for f in os.listdir(seed_dir) if os.path.isfile(os.path.join(seed_dir, f))]
    _envs = {"POC_DEBUG" : "1", "__POC_SHM_ID": str(shmid)} # @Adian: G^-_{tmp}

    for tog in open_tog_set:
        # print(tog)
        _envs[f'{TOG_PAT}{tog}'] = "1"  # @Adian: Switch on toggles and diasbled corresponding guards. -> Adding guards into G-

    global crash_detected_time_limit
    global revoke_seed_path
    
    revoke_seeds = list()

    # print(exec_parameter)
    max_time = 0.0
    for seed_file in seed_files:
        if '@@' not in exec_parameter:
            with open(seed_file, 'rb') as f:
                process = subprocess.Popen([exec_file,*exec_parameter], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=_envs,preexec_fn=disable_core)
        else:
            tmp_parameter = [seed_file if item == "@@" else item for item in exec_parameter]
            process = subprocess.Popen([exec_file,*tmp_parameter], stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=_envs,preexec_fn=disable_core)
        try:  
            stdout, stderr = process.communicate(timeout=crash_detected_time_limit)  
        except Exception as e:
            #Timeouts are not considered crashes for now
            process.kill()
            process.wait()
            return
              
        if process.returncode < 0 :
            revoke_seeds.append(seed_file)
            print(LOG,f"{len(revoke_seeds)}  {len(seed_files)} {process.returncode}")
            if len(revoke_seeds)> len(seed_files)*r1: #The current crash is a false positive caused by enabling the TOG
                return
    
    # len(seed_files)*r2 < len(revoke_seeds) <= len(seed_files)*r1
    # Randomly select len(seed_files) * r2 seeds from revoke_seeds
    if len(revoke_seeds) > len(seed_files)*r2:
        revoke_seeds = random.sample(revoke_seeds,int(len(seed_files)*r2))

    if len(revoke_seeds) != 0:
        print(f"we find {revoke_seeds} as revoke seeds")


    # If len(seed_files) * r2 >= len(revoke_seeds), do not make any changes
    for revoke_seed in revoke_seeds :
        revoke_seed_file = os.path.join(revoke_seed_path,os.path.basename(revoke_seed))
        if not os.path.exists(revoke_seed_file):
            shutil.copy2(revoke_seed,revoke_seed_file)



def single_run(exec_file: str,deq: deque,_envs: dict,exec_parameter:list,is_delete:bool = False) :
    global crash_detected_time_limit

    # print(exec_parameter)
    max_time = 0.0
    for seed_file in deq:
        return_code = 0
        start_time = time.time()
        if '@@' not in exec_parameter:
            with open(seed_file, 'rb') as f:
                process = subprocess.Popen([exec_file,*exec_parameter], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=_envs,preexec_fn=disable_core)
        else:
            tmp_parameter = [seed_file if item == "@@" else item for item in exec_parameter]
            process = subprocess.Popen([exec_file,*tmp_parameter], stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=_envs,preexec_fn=disable_core)
        try:  
            stdout, stderr = process.communicate(timeout=crash_detected_time_limit)  
        except Exception as e:
            print(LOG,"time out detected")
            process.kill()
            process.wait()
            return_code = -9
              
        cost_time = time.time()-start_time
        if max_time<cost_time:
            max_time=cost_time
        if return_code == 0:
            return_code = process.returncode
        if return_code < 0 :
            if is_delete == True:
                os.remove(seed_file)
                print(LOG,f"{seed_file} will erase crash when no tog is open , we will erase it")
            else :
                deq.remove(seed_file)
                deq.appendleft(seed_file)
                break
    return return_code,max_time

def build_deque(seed_dir: str):
    deq = deque()
    for seed_file in seed_dir:
        deq.appendleft(seed_file)
    return deq

def pessimistic_finder(origin_set : list, new_tog_set : list,seed_dir: str, exec_dir: str, exec_parameter: list,shmid :int):    # @Adian: Recognize and exclude rash toggles that lead to crash.

    global node_id_map
    global tmp_path

    result = set()


    # Get all files in seed_dir
    seed_files = [os.path.join(seed_dir, f) for f in os.listdir(seed_dir) if os.path.isfile(os.path.join(seed_dir, f))]
    _envs = {"POC_DEBUG" : "1", "__POC_SHM_ID": str(shmid)} # @Adian: G^-_{tmp}

    sorted_nodes = sorted(origin_set, key=lambda node: node_id_map[f'{TOG_PAT}{node}'], reverse=True)
    
    #Optimize deque
    deq = build_deque(seed_files)


    tog_set = sorted_nodes[::-1]

    pos = -1
    length = 1
    return_code = 0
    
    while pos + 1 < len(tog_set) :
        # print(LOG,f"pos: {pos},length: {length}")
        for tog in tog_set[pos+1:pos+1+length]:
            # print(tog)
            _envs[f'{TOG_PAT}{tog}'] = "1"  # @Adian: Switch on toggles and diasbled corresponding guards. -> Adding guards into G-
        # print(len(result))
        return_code,_ = single_run(exec_dir,deq,_envs,exec_parameter)
        if return_code < 0 :
            print(LOG,f"pos = {pos}  leng = {length} total =  {len(tog_set)} return_code = {return_code}")
            for tog in tog_set[pos+1:pos+1+length]: # @Adian: Switching off toggle through envs -> Removing guards from G- (recover G-)?
                del _envs[f'{TOG_PAT}{tog}'] # @Adian: Identified as rash guard and refuse to open it at this round.
            if length == 1 :
                revoke_seeds_finder(origin_set,seed_dir,exec_dir,exec_parameter,shmid)
                result.add(tog_set[pos+1])
                pos+=1
            else :
                length//=2
        else :
            pos+=length
            length*=2


    if len(result) == 0 : # A corner case.
        print(LOG,"opps,it's seem our bug finder lose it's effect")
        # print(LOG,f"open_set: {origin_set}")
        # print(LOG,f"new_set:{new_tog_set}")
        print(LOG,f"tog_set:{tog_set}")
        print(LOG,"we are going to use cmin as runner and run again")
        pos = -1
        length = 1
        return_code = 0
        target_cmd = [
            cmin_path,
            "-i", seed_dir,  # Input directory
            "-o", tmp_path,  # Output directory
            # "-t", str(timeout),  # Timeout duration
            # "-m", str(memory),  # Memory limit
            "-T", "1",
            "-t", str(round(cmin_time_limit*1000)),
            "--", 
            exec_dir, 
            *exec_parameter,
        ]
        while pos + 1 < len(tog_set) :
            # print(LOG,f"pos: {pos},length: {length}")
            for tog in tog_set[pos+1:pos+1+length]:
                # print(tog)
                _envs[f'{TOG_PAT}{tog}'] = "1"
            # print(len(result))
            flush_file(tmp_path)
            # return_code,_ = single_run(exec_dir,deq,_envs,exec_parameter)
            result2=subprocess.run(target_cmd, env=_envs, stdin=sys.stdin, stdout=DEVNULL, stderr=DEVNULL)
            if result2.returncode != 0 :
                print(LOG,f"pos = {pos}  leng = {length} total =  {len(tog_set)} return_code = {result2.returncode}")
                for tog in tog_set[pos+1:pos+1+length]:
                    del _envs[f'{TOG_PAT}{tog}'] # @Adian: Identified as rash guard and refuse to open it at this round.
                if length == 1 :
                    result.add(tog_set[pos+1])
                    pos+=1
                else :
                    length//=2
            else :
                pos+=length
                length*=2
        # exit(0)

    return result

# Topological sort function
def topological_sort(graph):
    visited = set()
    stack = []

    def dfs(node):  # @Adian: Sort via DFS
        if node in visited:
            return
        visited.add(node)
        for neighbor in graph.get(node, []):
            dfs(neighbor)   # @Adian: Does neighbor refer to siblings?
        stack.append(node)

    # Perform DFS on each node
    for node in graph:
        if node not in visited:
            dfs(node)
    
    # Return the elements in the stack from top to bottom as the topological order
    return stack[::-1]  # @Adian: Generate a list of reversing order.

def flush_file(dest_dir) :
    # Create the destination directory if it does not exist
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    # Clear the contents of the destination directory
    for item in os.listdir(dest_dir):
        item_path = os.path.join(dest_dir, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)


def move_files_and_clear(src_dir, dest_dir):
    # Ensure the source directory exists
    if not os.path.exists(src_dir):
        print(LOG,"src_dir don't exist")
        return
    
    flush_file(dest_dir)
    
    # Move all files from the source directory to the destination directory
    for item in os.listdir(src_dir):
        item_path = os.path.join(src_dir, item)
        if item.startswith('.') and os.path.isfile(item_path):
            os.remove(item_path)
            continue
        shutil.move(os.path.join(src_dir, item), dest_dir)
    
    # Clear the source directory (may contain hidden files)
    for item in os.listdir(src_dir):  
        item_path = os.path.join(src_dir, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)
    

def are_filenames_identical(dir1: str, dir2: str) -> bool:
    """Check whether the non-hidden filenames in two directories match exactly"""
    def get_filenames(directory: str):
        return {f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and not f.startswith('.')}

    return get_filenames(dir1) == get_filenames(dir2)   

def delete_hidden_files_and_dirs(directory: str):
    """Delete all hidden files and hidden directories (including their contents) in the specified directory"""
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        return

    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        # Check if it is a hidden file or hidden directory (starts with '.')
        if item.startswith("."):
            try:
                if os.path.isfile(item_path):  # Hidden file
                    os.remove(item_path)
                elif os.path.isdir(item_path):  # Hidden directory
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"删除 {item_path} 失败: {e}")

def main():

    # Parse cmd.
    # argv, target_cmd, use_stdin = parse_target_cmd()
    # print(LOG, 'argv:', argv)
    # print(LOG, 'target_cmd:', target_cmd)

    global result
    global node_id_map 
    global time_limit
    global crash_detected_time_limit
    global cmin_time_limit
    global cmin_path
    global tmp_path
    global revoke_seed_path
    start_time = time.time()

    
    # for dfs topsort
    sys.setrecursionlimit(10**6)

    # Parse real args
    if '--' not in sys.argv[1:] :
        print('please use -- to split poff parameter with exec file parameter')
        exit(0)



    cmd_parser = build_arg_parser()
    args = cmd_parser.parse_args(sys.argv[1:sys.argv.index('--')])
    in_dir = os.path.abspath(args.in_dir)
    out_dir = os.path.abspath(args.out_dir)
    graph_dir = os.path.abspath(args.graph_dir)
    exec_dir = os.path.abspath(args.exec)
    exec_file_name = os.path.basename(exec_dir)
    thread_num = args.task
    quiet = args.quiet
    num_tog = args.num_toggle
    time_limit_poff = args.TimeOut
    exec_parameter = sys.argv[sys.argv.index('--')+1:]
    print(exec_parameter)
    if args.num_tog_dump is not None:
        print(LOG, 'Detect dump file. May overwrite given toggle number.')
        dump_file = os.path.abspath(args.num_tog_dump)
        with open(dump_file, 'r') as f:
            num_tog = int(f.readline().strip())
        print(LOG, f'Read num_tog {num_tog} from: {dump_file}.')
    map_size = num_tog + 1
    

    #Calculate the timeout duration
    seed_files = [os.path.join(in_dir, f) for f in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, f))]
    return_code,time_limit = single_run(exec_dir,build_deque(seed_files),{},exec_parameter,True)

    # if return_code < 0 :
    #     print(LOG,f"return code = {return_code}, the origin seed will erase crash,plase checkout")
    #     exit(0)

    time_limit = time_limit * 20
    
    if time_limit < min_time_limit :
        time_limit = min_time_limit
    if time_limit > max_time_limit :
        time_limit = max_time_limit
    crash_detected_time_limit = time_limit
    cmin_time_limit = time_limit
    print(LOG,f"the max time limit is set to {time_limit}")

    # Read DOT data using pydot
    print(LOG,f'we are parsing dot file from {graph_dir}')
    graphs = pydot.graph_from_dot_file(graph_dir)
    graph = graphs[0]

    # Create a directed graph
    G = nx.DiGraph()

    # Add edges from DOT data to the directed graph
    for edge in graph.get_edges():
        src = edge.get_source()
        dst = edge.get_destination()
        G.add_edge(src, dst)

    # Build a dictionary
    adjacency_dict = {}
    for node in G.nodes():
        # some corner case 
        adjacency_dict[node] = list(G.successors(node))

    # Perform topological sort
    topo_sorted_nodes = topological_sort(adjacency_dict)

    # Assign IDs
    node_id_map = {node: i for i, node in enumerate(topo_sorted_nodes)}

    # output
    # print("Topological sort result:", topo_sorted_nodes)
    # print("Node ID assignment:", node_id_map)

    # exit(0)

    #####################
    # Start core logics #
    #####################

    # Load lots of shm functions from C library.
    c_shmget = load_c_shmget()
    c_shmctl = load_c_shmctl()
    c_shmat = load_c_shmat()
    c_shmdt = load_c_shmdt()

    # Load a shm
    shm_id = c_shmget(IPC_PRIVATE, map_size, IPC_CREAT | IPC_EXCL | DEFAULT_PERMISSION)
    shm = load_shm(cshmat=c_shmat, shmid=shm_id, cdtype=c_uint8, shmlen=map_size)
    # print(shm[0][0])    # Read data from the shm like this.

    # Execute test cases and update global tog_map
    print(LOG, 'Execute testcases...')

    turn_num = 1
    open_tog_set = set()        # @Adian: O, G^- set of all the disabled guards. 
    parse_coverage_set = set()  # incremental   -> @Adian: O_new, set of newly disabled guards.
    ban_tog_set = set() # some toggle cannot open -> @Adian: R, set of reckless guards
    new_tog_set = set()

    # with open("./ban_tog", 'r') as file:
    #     content = file.read()
    
    # Match all numbers using regular expressions
    # numbers = re.findall(r'\d+', content)
    
    # Add the matched numbers to a set
    # for number in numbers:
    #     ban_tog_set.add(int(number))


    # input_dir = in_dir
    current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    timeout_duration = datetime.timedelta(seconds=time_limit_poff)+datetime.datetime.now()

    print(LOG,f"poff will be stop forced in {timeout_duration}")

    output_file = f"{current_date}_cmin_{exec_file_name}_{turn_num}"
    output_path = os.path.join(out_dir, output_file)
    output_path = os.path.join(out_dir, output_file)
    revoke_seed_path = os.path.join(out_dir,f"{current_date}_revoke_{exec_file_name}_{turn_num}")
    os.makedirs(revoke_seed_path, exist_ok=True)
    last_output_path = ""
    tmp_path = f"/tmp/{exec_file_name}_tmp"
    # create_or_clear_directory(output_path)

    work_path = os.environ.get("AFLPP")
    print(LOG,work_path)
    cmin_path = os.path.join(work_path, "afl-cmin")


    while True:
        
        print(LOG, f"round : {turn_num}")
        target_cmd = [
            cmin_path,
            "-i", in_dir,  # Input directory
            "-o", output_path,  # Output directory
            # "-t", str(timeout),  # Timeout duration
            # "-m", str(memory),  # Memory limit
            "-T", thread_num,
            "-t", str(round(cmin_time_limit*1000)),
            "--", 
            exec_dir, 
            *exec_parameter,
        ]
        print(LOG, f"run : {' '.join(target_cmd)}")
        
        # we hope to recode the follow stuff :  # @Adian: tog_set (\Pi) -> *passed guards*, rash guards, outermost guards.
        # the tog we have open 
        # the tog reached in new round
        # the seeds filtered by cmin with the tog we have open
        tog_set =   execute_cases_and_update_map(   # @Adian: Cmin also in this round.
                    open_tog_set=open_tog_set, cmd=target_cmd, shmid=shm_id, togshm=shm,
                    mapsize=map_size, be_quiet=quiet)

        delete_hidden_files_and_dirs(output_path)

        if result.returncode != 0 : # @Adian: Case-1: rash toggles leading to crash.
            #Segmentation fault occurred
            print(LOG,f"In this round, some seeds triggered crashes or timeouts .\n" 
                  f"We're going to identify the toggle that caused the issue and ensure it's never activated again.")
            
            
            # Identify the false-positive seeds
            revoke_seeds_finder(open_tog_set,in_dir,exec_dir,exec_parameter,shm_id)
            # bad_tog = optimistic_finder(open_tog_set,sorted_nodes,last_output_path,exec_dir,std,shm_id)
            bad_tog = pessimistic_finder(open_tog_set,new_tog_set,in_dir,exec_dir,exec_parameter,shm_id)

            if len(bad_tog) == 0 :
                print(LOG,"we can't find any tog to ban, it's may blame to the the efficiency difference between cmin and crash detection")
                print(LOG,"decrease the time limit of crash detection to 75% and and time limit of cmin to 110% to try angain")
                crash_detected_time_limit = crash_detected_time_limit * 0.75
                cmin_time_limit = cmin_time_limit * 1.5
                continue
                                
            print(LOG,f"we find {bad_tog} as banned tog in this turn")
            ban_tog_set = ban_tog_set.union(bad_tog)
            open_tog_set.difference_update(bad_tog)
            new_tog_set.difference_update(bad_tog)
            parse_coverage_set.difference_update(bad_tog)
            continue    # @Adian: Handle crashing-reckless, then to next round and try again.
            
        if last_output_path != "" and are_filenames_identical(output_path,last_output_path) :
            for item in os.listdir(output_path) :
                print(item+'\n')
            #This round’s enabled TOG caused cmin to produce only one file # @Adian: Case-2: rash toggles sharp convergence, which acts like a fake fixed point.
            print(LOG,f"In this round, the output of cmin results in only one file .\n" 
                  f"We're going to identify the toggle that caused the issue and ensure it's never activated again.")
            
            move_files_and_clear(output_path,tmp_path)  # @Adian: Copy seeds heterogeneous in the recent two rounds.
            target_cmd = [  # @Adian: Reorgianize the command for cmin.
                cmin_path,
                "-i", tmp_path,  # Input directory
                "-o", output_path,  # Output directory
                # "-t", str(timeout),  # Timeout duration
                # "-m", str(memory),  # Memory limit
                "-T", thread_num,
                "-t", str(round(cmin_time_limit*1000)),
                "--", 
                exec_dir, 
                *exec_parameter,
            ]
            bad_tog =   execute_cases_and_update_map(
                    open_tog_set=open_tog_set, cmd=target_cmd, shmid=shm_id, togshm=shm,
                    mapsize=map_size, be_quiet=quiet)
            bad_tog = bad_tog & open_tog_set    # @Adian: Rash toggle candidates. The guards covered by the hetergenous seeds are the rash guards.
            if len(bad_tog) != 0:
                print(LOG,f"we find {len(bad_tog)} banned tog ")
                ban_tog_set = ban_tog_set.union(bad_tog)
                open_tog_set.difference_update(bad_tog)
                new_tog_set.difference_update(bad_tog)
                # parse_coverage_set.difference_update(bad_tog) # @Adian: O_new
                shutil.rmtree(output_path)
                continue    # @Adian: Handle converging-reckless, then to next round and try again.
            else :
                print(LOG,f"no ban tog is found,if this happens,please check if {len(new_tog_set)} == 0 )")
                new_tog_set = set()

        # @Adian: \Pi passed guards tog_set 
        new_tog_set =tog_set-open_tog_set-ban_tog_set   # @Adian: Determine outermost guards by *coverage*.
        # print(tog_set)

        if len(new_tog_set) == 0 :  # @Adian: new_tog -> newly covered guards above; outermost guards in this part. -> Locate outermost guards but do not disable them at this round.
            old_len = len(open_tog_set)
            print(LOG,f"no new tog triggered , we are going to open it actively")
            
            open_tog_queue = deque()  

            for node in parse_coverage_set :    # @Adian: dQ <- O, parse_coverage_set is O
                open_tog_queue.append(f'{TOG_PAT}{node}')
                    # if out_node[:7] != "POC_TOG" :
                    #     if len(adjacency_dict[out_node]) > 1 :
                    #         log("out_node is NONE_TOG_BB but has tow branch , ")
                    # number = int(out_node.split('_')[-1])  # Take the last part and convert it to an integer
                    # if number not in open_tog_set:
                    #     open_tog_set.add(number)
                    #     new_tog_set.add(number)
            #we will do bfs search to find some tog
            temp_set = set()    # @Adian: checked
            while len(open_tog_queue) > 0:
                # print(len(open_tog_queue))
                head = open_tog_queue[0]
                open_tog_queue.popleft() # @Adian: deque, pop left for each.
                if head in temp_set :
                    continue
                temp_set.add(head)
                # if head[:7] == "POC_TOG" :
                #     number = int(head.split('_')[-1])
                #     # if number in ban_tog_set :
                #     #     continue
                #     if number not in open_tog_set :
                #         open_tog_set.add(number)
                #         new_tog_set.add(number)
                #         continue

                for out_node in adjacency_dict[head] :  # @Adian: GetSuccessors[g]
                    if out_node[:7] == "POC_TOG" :
                        number = int(out_node.split('_')[-1])
                        if number not in parse_coverage_set and \
                            number not in ban_tog_set and \
                            number not in open_tog_set  :   # @Adian: Should not in O_new (parse_coverage_set), should not in R (ban_tog), should not in G^- (open_tog).
                            new_tog_set.add(number)     # @Adian: Collect outermost guards
                            open_tog_set.add(number)    # @Adian: Disable outermost guards, G^- \cup \Omega
                        continue
                    open_tog_queue.append(out_node)


            parse_coverage_set = new_tog_set    # @Adian: O is \Omega because P
            
            if len(open_tog_set) == old_len :   # @Adian: open_tog_set = G^-, only used for checking the fixed point.
                print(LOG,"no tog can be open actively! quit")
                break   # @Adian: Reach a real fixed point: No covered guards and no outermost guards can be opened.
        else :
            open_tog_set |= new_tog_set
            parse_coverage_set |= new_tog_set

        # print(f"some togs are added : {new_tog_set}")
        # print(f"now the follow togs are keeping open : {open_tog_set}")
        print(LOG,f"now we have {len(open_tog_set)} tog")

        if datetime.datetime.now()>timeout_duration:
            print(LOG,f"poff time out")
            break

        turn_num = turn_num + 1
        current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")   # @Adian : Timer
        output_file = f"{current_date}_cmin_{exec_file_name}_{turn_num}"
        revoke_seed_path = os.path.join(out_dir,f"{current_date}_revoke_{exec_file_name}_{turn_num}")
        os.makedirs(revoke_seed_path, exist_ok=True)
        last_output_path = output_path
        output_path = os.path.join(out_dir, output_file)

        print(LOG,f"next round we will use {in_dir} as seed and {output_path} as cmin output")

    # Free the shm  # @Adian: all done, deinitilized
    c_shmdt(shm) 
    c_shmctl(shm_id, IPC_RMID, 0)

    # Done
    print(LOG, LOG_DELIM)
    print(LOG, "We are done here, have a nice day :-)")
    print(LOG, LOG_DELIM)

    end_time = time.time()

    print(LOG,f"the total time cost is {(end_time-start_time)}s")


    current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")   # @Adian : Timer
    output_file = f"{current_date}_cmin_{exec_file_name}_{turn_num+1}"
    output_path = os.path.join(out_dir, output_file)
    os.makedirs(output_path, exist_ok=True)
    

# Entry point
if __name__ == '__main__':
    main()
