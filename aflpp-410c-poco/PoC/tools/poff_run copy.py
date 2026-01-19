"""
To run given test inputs (seeds) and collect the toggles
that has been passed. 
"""

import os
import copy
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

from collections import deque
from tqdm import tqdm
from subprocess import DEVNULL
from poccshm import *


# Default TOG_MAP_SIZE = 1 << 16, so the default number should -2
DEFAULT_TOG_NUM = (1 << 16) 
result = None
tmp_path = ""
time_limit = 2
node_id_map = {}



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
    _p.add_argument('--stdin', '-s', required=False, action='store_true',
                    help='Whether use the stdin as input.')
    _p.add_argument('--task', '-t', required=False, type=str,default='1',
                    help='how many parallel tasks to run (default: 1, all=nproc)')
    return _p

def count_files_in_directory(directory):
    # Get all files and folders in the directory
    entries = os.listdir(directory)
    
    # Filter out hidden files
    files = [entry for entry in entries if not entry.startswith(".") and os.path.isfile(os.path.join(directory, entry))]
    
    # Return the number of files
    return len(files)



def single_run(exec_file: str,deq: deque,_envs: dict,use_stdin:bool) :
    global count

    max_time = 0.0
    for seed_file in deq:
        return_code = 0
        start_time = time.time()
        if use_stdin:
            with open(seed_file, 'rb') as f:
                process = subprocess.Popen([exec_file], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=_envs)
        else:
            process = subprocess.Popen([exec_file, seed_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE,env=_envs)

        try:
            stdout, stderr = process.communicate(timeout=time_limit)
        except Exception as e:
            process.kill()
            process.wait()
        cost_time = time.time()-start_time
        if max_time<cost_time:
            max_time=cost_time
        return_code = process.returncode
        if return_code < 0 :
            deq.remove(seed_file)
            deq.appendleft(seed_file)
            break
    return return_code,max_time

def build_deque(seed_dir: str):
    deq = deque()
    for seed_file in seed_dir:
        deq.appendleft(seed_file)
    return deq

def pessimistic_finder(origin_set : list, new_tog_set : list,seed_dir: str, exec_dir: str, use_stdin: bool,shmid :int):

    result = set()


    # Get all files in seed_dir
    seed_files = [os.path.join(seed_dir, f) for f in os.listdir(seed_dir) if os.path.isfile(os.path.join(seed_dir, f))]
    _envs = {"POC_DEBUG" : "1", "__POC_SHM_ID": str(shmid)}
    # print(LOG,f'orgin_set : {origin_set}')
    # print(LOG,f'tog_set : {tog_set}')
    # print(LOG,f'seed_dir : {seed_dir}')
    # print(LOG,f'exec_dir : {exec_dir}')
    # print(LOG,f'use_stdin : {use_stdin}')
    # print(LOG,f'shmid : {shmid}')
    # for _ in origin_set:
    #     if _ not in tog_set:
    #         _envs[f'{TOG_PAT}{_}'] = "1"

    #First, check which part caused the crash
    for _ in origin_set:
            _envs[f'{TOG_PAT}{_}'] = "1"

    return_code,_ = single_run(exec_dir,seed_files,_envs,use_stdin)

    if return_code == 0 :
        print(LOG,"the new_tog_set erase the crash")
        sorted_nodes = sorted(new_tog_set, key=lambda node: node_id_map[f'{TOG_PAT}{node}'], reverse=True) 
    else :
        print(LOG,"have no idea where erase the crash")
        _envs = {"POC_DEBUG" : "1", "__POC_SHM_ID": str(shmid)}
        sorted_nodes = sorted(origin_set, key=lambda node: node_id_map[f'{TOG_PAT}{node}'], reverse=True)
    
    #Optimize deque
    deq = build_deque(seed_files)


    tog_set = sorted_nodes[::-1]

    pos = -1
    length = 1
    return_code = 0
    
    while pos + 1 < len(tog_set) :
        print(LOG,f"pos: {pos},length: {length}")
        for tog in tog_set[pos+1:pos+1+length]:
            # print(tog)
            _envs[f'{TOG_PAT}{tog}'] = "1"
        # print(len(result))
        return_code,_ = single_run(exec_dir,deq,_envs,use_stdin)
        if return_code < 0 :
            print(f"pos = {pos}  leng = {length} total =  {len(tog_set)} return_code = {return_code}")
            for tog in tog_set[pos+1:pos+1+length]:
                del _envs[f'{TOG_PAT}{tog}'] 
            if length == 1 :
                result.add(tog_set[pos+1])
                pos+=1
            else :
                length//=2
        else :
            pos+=length
            length*=2

    return result

# Topological sort function
def topological_sort(graph):
    visited = set()
    stack = []

    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        for neighbor in graph.get(node, []):
            dfs(neighbor)
        stack.append(node)

    # Perform DFS on each node
    for node in graph:
        if node not in visited:
            dfs(node)
    
    # Return the elements in the stack from top to bottom as the topological order
    return stack[::-1]


def move_files_and_clear(src_dir, dest_dir):
    # Ensure the source directory exists
    if not os.path.exists(src_dir):
        print("Source directory does not exist")
        return
    
    # Create the destination directory if it does not exist
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    # Clear the destination directory
    for item in os.listdir(dest_dir):
        item_path = os.path.join(dest_dir, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)
    
    # Move all files from the source directory to the destination directory
    for item in os.listdir(src_dir):
        item_path = os.path.join(src_dir, item)
        # Remove hidden files in the source directory
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

def main():

    # Parse cmd.
    # argv, target_cmd, use_stdin = parse_target_cmd()
    # print(LOG, 'argv:', argv)
    # print(LOG, 'target_cmd:', target_cmd)

    global result
    global node_id_map 
    global time_limit
    start_time = time.time()


    
    # for dfs topsort
    sys.setrecursionlimit(10**6)

    # Parse real args
    cmd_parser = build_arg_parser()
    args = cmd_parser.parse_args(sys.argv[1:])
    in_dir = os.path.abspath(args.in_dir)
    out_dir = os.path.abspath(args.out_dir)
    graph_dir = os.path.abspath(args.graph_dir)
    exec_dir = os.path.abspath(args.exec)
    exec_file_name = os.path.basename(exec_dir)
    thread_num = args.task
    quiet = args.quiet
    num_tog = args.num_toggle
    std = args.stdin
    if args.num_tog_dump is not None:
        print(LOG, 'Detect dump file. May overwrite given toggle number.')
        dump_file = os.path.abspath(args.num_tog_dump)
        with open(dump_file, 'r') as f:
            num_tog = int(f.readline().strip())
        print(LOG, f'Read num_tog {num_tog} from: {dump_file}.')
    map_size = num_tog + 1
    

    #Calculate the timeout duration
    seed_files = [os.path.join(in_dir, f) for f in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, f))]
    return_code,time_limit = single_run(exec_dir,build_deque(seed_files),{},std)

    if return_code != 0 :
        print(LOG,"the origin seed will erase crash,plase checkout")
        exit(0)

    time_limit = time_limit * 5
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

    # Build an adjacency dictionary
    adjacency_dict = {}
    for node in G.nodes():
        # some corner case 
        adjacency_dict[node] = list(G.successors(node))

    # Perform topological sort
    topo_sorted_nodes = topological_sort(adjacency_dict)

    # Assign IDs to nodes
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

    round = 1
    open_tog_set = set()
    parse_coverage_set = set()  # incremental
    ban_tog_set = set() # some toggle can't not open
    new_tog_set = set()

    # with open("./ban_tog", 'r') as file:
    #     content = file.read()
    
    # Match all numbers using regular expressions
    # numbers = re.findall(r'\d+', content)
    
    # Add the matched numbers to a set
    # for number in numbers:
    #     ban_tog_set.add(int(number))


    # input_dir = in_dir
    current_date = datetime.datetime.now().strftime("%Y%m%d%H%M")
    output_file = f"{current_date}_cmin_{exec_file_name}_{round}"
    output_path = os.path.join(out_dir, output_file)
    last_output_path = ""
    tmp_path = f"/tmp/{exec_file_name}_tmp"
    # create_or_clear_directory(output_path)

    work_path = os.environ.get("AFLPP")
    print(work_path)
    cmin_path = os.path.join(work_path, "afl-cmin")
    while True:
        
        print(LOG, f"round : {round}")
        target_cmd = [
            cmin_path,
            "-i", in_dir,  # Input directory
            "-o", output_path,  # Output directory
            # "-t", str(timeout),  # Timeout duration
            # "-m", str(memory),  # Memory limit
            "-T", thread_num,
            "-t", str(2000),
            "--", 
            exec_dir, 
            "" if std else "@@",
        ]
        print(LOG, f"run : {' '.join(target_cmd)}")
        
        # we hope to recode the follow stuff :
        # the tog we have open
        # the tog reached in new round
        # the seeds filtered by cmin with the tog we have open
        tog_set =   execute_cases_and_update_map(
                    open_tog_set=open_tog_set, cmd=target_cmd, shmid=shm_id, togshm=shm,
                    mapsize=map_size, be_quiet=quiet)

        if result.returncode != 0 :
            #A segmentation fault occurred, or enabling this TOG resulted in cmin producing only a single file
            print(f"In this round, some seeds triggered crashes or timeouts .\n" 
                  f"We're going to identify the toggle that caused the issue and ensure it's never activated again.")
            
            

            # bad_tog = optimistic_finder(open_tog_set,sorted_nodes,last_output_path,exec_dir,std,shm_id)
            bad_tog = pessimistic_finder(open_tog_set,new_tog_set,last_output_path,exec_dir,std,shm_id)
                
                                
            print(LOG,f"we find {bad_tog} as banned tog in this turn")
            ban_tog_set = ban_tog_set.union(bad_tog)
            open_tog_set.difference_update(bad_tog)
            new_tog_set.difference_update(bad_tog)
            parse_coverage_set.difference_update(bad_tog)
            continue
            
        if last_output_path != "" and are_filenames_identical(output_path,last_output_path) :
            for item in os.listdir(output_path) :
                print(item+'\n')
            #Enabling this TOG in this round caused cmin to produce only a single file
            print(f"In this round, the output of cmin results in only one file .\n" 
                  f"We're going to identify the toggle that caused the issue and ensure it's never activated again.")
            
            move_files_and_clear(output_path,tmp_path)
            target_cmd = [
                cmin_path,
                "-i", tmp_path,  # Input directory
                "-o", output_path,  # Output directory
                # "-t", str(timeout),  # Timeout duration
                # "-m", str(memory),  # Memory limit
                "-T", thread_num,
                "-t", str(2000),
                "--", 
                exec_dir, 
                "" if std else "@@",
            ]
            bad_tog =   execute_cases_and_update_map(
                    open_tog_set=open_tog_set, cmd=target_cmd, shmid=shm_id, togshm=shm,
                    mapsize=map_size, be_quiet=quiet)
            if len(bad_tog) != 0:
                print(LOG,f"we find {len(bad_tog)} banned tog ")
                ban_tog_set = ban_tog_set.union(bad_tog)
                open_tog_set.difference_update(bad_tog)
                new_tog_set.difference_update(bad_tog)
                # parse_coverage_set.difference_update(bad_tog)
                shutil.rmtree(output_path)
                continue
            else :
                print(LOG,f"no ban tog is found,if this happens,please check if {len(new_tog_set)} == 0 )")


        new_tog_set =tog_set-open_tog_set-ban_tog_set

        if len(new_tog_set) == 0 :
            old_len = len(open_tog_set)
            print(f"no new tag triggered , we are going to open it actively")
            
            open_tog_queue = deque()

            for node in parse_coverage_set :
                open_tog_queue.append(f'{TOG_PAT}{node}')
                    # if out_node[:7] != "POC_TOG" :
                    #     if len(adjacency_dict[out_node]) > 1 :
                    #         log("out_node is NONE_TOG_BB but has tow branch , ")
                    # number = int(out_node.split('_')[-1])  # Take the last part and convert it to an integer
                    # if number not in open_tog_set:
                    #     open_tog_set.add(number)
                    #     new_tog_set.add(number)
            #we will do bfs search to find some tog
            temp_set = set() 
            while len(open_tog_queue) > 0:
                # print(len(open_tog_queue))
                head = open_tog_queue[0]
                open_tog_queue.popleft()
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

                for out_node in adjacency_dict[head] :
                    if out_node[:7] == "POC_TOG" :
                        number = int(out_node.split('_')[-1])
                        if number not in parse_coverage_set and \
                            number not in ban_tog_set and \
                            number not in open_tog_set  :
                            new_tog_set.add(number)
                            open_tog_set.add(number)
                        continue
                    open_tog_queue.append(out_node)


            parse_coverage_set = new_tog_set
            
            if len(open_tog_set) == old_len :
                print("no tog can be open actively! quit")
                break
            else :
                open_tog_set |= new_tog_set
                parse_coverage_set |= new_tog_set

        # print(f"some togs are added : {new_tog_set}")
        # print(f"now the follow togs are keeping open : {open_tog_set}")
        print(f"now we have {len(open_tog_set)} tog")
        round = round + 1

        # input_dir = output_path
        current_date = datetime.datetime.now().strftime("%Y%m%d%H%M")
        output_file = f"{current_date}_cmin_{exec_file_name}_{round}"
        last_output_path = output_path
        output_path = os.path.join(out_dir, output_file)

        print(f"next round we will use {in_dir} as seed and {output_path} as cmin output")

    # Free the shm
    c_shmdt(shm) 
    c_shmctl(shm_id, IPC_RMID, 0)

    # Done
    print(LOG, LOG_DELIM)
    print(LOG, "We are done here, have a nice day :-)")
    print(LOG, LOG_DELIM)

    end_time = time.time()

    print(f"the total time cost is {(end_time-start_time)}s")
    

# Entry point
if __name__ == '__main__':
    main()
