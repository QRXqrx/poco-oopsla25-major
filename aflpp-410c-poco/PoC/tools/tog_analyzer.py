"""
To run given test inputs (seeds) and collect the toggles
that has been passed. 
"""

import os
import copy
import shutil
import argparse
import subprocess
import numpy as np
import pandas as pd

from tqdm import tqdm
from subprocess import DEVNULL
from poccshm import *


# Default TOG_MAP_SIZE = 1 << 16, so the default number should -2
DEFAULT_TOG_NUM = (1 << 16) 


def run_target_poc(target_args: list, shmid: int, 
                   stdin=None, be_quiet: bool =False):
    _envs = {"POC_DEBUG" : "1", "__POC_SHM_ID": str(shmid)}
    if be_quiet:
        subprocess.run(target_args, env=_envs, stdin=stdin, stdout=DEVNULL, stderr=DEVNULL)
    else:
        print(LOG, 'Run target_args:', target_args)
        print(LOG, '+++++++++++++++ Program Outputs +++++++++++++++ ')
        subprocess.run(target_args, env=_envs, stdin=stdin)
        print(LOG, '+++++++++++++++++++++++++++++++++++++++++++++++ ')


def execute_cases_and_update_map(
        casedir: str, 
        cmd: list, 
        shmid: int, togshm,
        mapsize: int = DEFAULT_TOG_NUM,
        use_stdin: bool = False,
        be_quiet: bool = False) -> np.array:
    """ 
    Execute every test cases inside the given casedir and return 
    the resultant toggle map.
    """
    # Prepare 
    _tog_map = np.zeros(mapsize)
    # Execute test cases
    _case_cnt = 0
    _sorted_cases = sorted(os.listdir(casedir))
    for _ in tqdm(_sorted_cases, desc=f'{LOG} Processing {len(_sorted_cases)} test cases'):
        if _.startswith('.'):
            continue
        _path = os.path.join(casedir, _)
        if os.path.isdir(_path):
            raise RuntimeError('Cannot handle nested test case dir!')
        # Copy cmd
        _cmd = copy.deepcopy(cmd)
        # Judge type and run.
        if use_stdin:
            # use_stdin, use file instream as input.
            with open(_path, 'r') as _istream:
                run_target_poc(_cmd, shmid=shmid, stdin=_istream, 
                               be_quiet=be_quiet)
        else:
            # use_file, replace @@ with the path to the file.            
            _idx = _cmd.index(FILEIN_LOC)
            _cmd[_idx] = _path
            run_target_poc(_cmd, shmid=shmid, be_quiet=be_quiet)  
        # Update global tog map.
        for _i in range(1, mapsize):
            if togshm[0][_i]:
                _tog_map[_i] += 1
                # Clean shm
                togshm[0][_i] = 0
        # Count case
        _case_cnt += 1
    return _tog_map, _case_cnt


def parse_tog_dict(map: np.ndarray) -> dict:
    _data = dict()
    for _ in range(1, map.size):
        _data[f'{TOG_PAT}{_}'] = map[_]
    return _data


def write_tog_cnt_csv(odir: str, data: dict):
    _csv = os.path.join(odir, 'tog_cnt.csv')
    pd.DataFrame(data=data, index=['tog_cnt'], dtype='int').to_csv(_csv)
    print(LOG, 'Write toggle counts to:', _csv)


def gen_unset_all_script(odir: str, ntog: int):
    _unset_script = os.path.join(odir, 'unset_all.sh')
    _lines = ['#!/bin/bash\n', '\n']
    for _ in range(1, ntog+1):
        _tog_id = f'{TOG_PAT}{_}'
        _lines.append(f'unset {_tog_id} \n')
    # Write unset
    with open(_unset_script, 'w') as _file:
        _file.writelines(_lines)
    print(LOG, 'Write script to unset all toggles to:', _unset_script)


def gen_setup_script(odir: str, togdict: dict, ncase: int, type: str = "notzero"):
    _setup_script = os.path.join(odir, f'setup_{type}.sh')
    _lines = ['#!/bin/bash\n', '\n']
    for _tog_id in sorted(list(togdict.keys())):
        _tog_hit = togdict[_tog_id]
        if type == 'notzero':
            _doappend = (_tog_hit > 0)
        elif type == 'zero':
            _doappend = (_tog_hit == 0)
        elif type == 'hitall': 
            _doappend = (_tog_hit == ncase)
        elif type == 'hitmid': # Greater than zero but less then not all 
            _doappend = (_tog_hit > 0 and _tog_hit < ncase)
        else:
            raise RuntimeError(f"Unrecognized type: {type}")
        if _doappend:  # Append a export line if match append condition.
            _lines.append(f'export {_tog_id}=1 \n')
    # Write unset
    with open(_setup_script, 'w') as _file:
        _file.writelines(_lines)
    print(LOG, f'Write script to setup toggles ({type}) to:', _setup_script)


def build_arg_parser() -> argparse.ArgumentParser:
    """
    Build command line argument parser.
    :return: Arg parser instance.
    """
    _p = argparse.ArgumentParser()
    _p.add_argument('--in_dir', '-i', required=True, type=str,
                    help='Directory storing test cases.')
    _p.add_argument('--out_dir', '-o', required=True, type=str,
                    help='Directory to output toggle analysis results.')
    _p.add_argument('--num_toggle', '-n', required=False, type=int, default=DEFAULT_TOG_NUM,
                    help='Directory to output toggle analysis results.')
    _p.add_argument('--num_tog_dump', '-N', required=False, type=str, default=None,
                    help='Dump file recording toggle number.')
    _p.add_argument('--quiet', '-q', required=False, action='store_true',
                    help='Whether hide target output.')
    return _p


def main():

    # Parse cmd.
    argv, target_cmd, use_stdin = parse_target_cmd()
    print(LOG, 'argv:', argv)
    print(LOG, 'target_cmd:', target_cmd)

    # Parse real args
    cmd_parser = build_arg_parser()
    args = cmd_parser.parse_args(argv)
    in_dir = os.path.abspath(args.in_dir)
    out_dir = os.path.abspath(args.out_dir)
    quiet = args.quiet
    num_tog = args.num_toggle
    if args.num_tog_dump is not None:
        print(LOG, 'Detect dump file. May overwrite given toggle number.')
        dump_file = os.path.abspath(args.num_tog_dump)
        with open(dump_file, 'r') as f:
            num_tog = int(f.readline().strip())
        print(LOG, f'Read num_tog {num_tog} from: {dump_file}.')
    map_size = num_tog + 1

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
    tog_map, num_case = execute_cases_and_update_map(
        casedir=in_dir, cmd=target_cmd, shmid=shm_id, togshm=shm,
        mapsize=map_size, use_stdin=use_stdin, be_quiet=quiet)

    # Free the shm
    c_shmdt(shm) 
    c_shmctl(shm_id, IPC_RMID, 0)

    print(tog_map)

    # Write result to local.
    print(LOG, LOG_DELIM)
    if os.path.exists(out_dir):
        print(LOG, f"Out dir exists `{out_dir}`. We will recreate it.")
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    # Postprocess
    print(LOG, 'Parse tog_shm...')
    tog_dict = parse_tog_dict(map=tog_map)
    print(LOG, 'tog_dict_size', len(tog_dict), "num_tog", num_tog)
    print(LOG, 'Writing results...')
    write_tog_cnt_csv(odir=out_dir, data=tog_dict)
    gen_unset_all_script(odir=out_dir, ntog=num_tog)
    gen_setup_script(odir=out_dir, togdict=tog_dict, ncase=num_case, type='notzero')
    gen_setup_script(odir=out_dir, togdict=tog_dict, ncase=num_case, type='zero')
    gen_setup_script(odir=out_dir, togdict=tog_dict, ncase=num_case, type='hitall')
    gen_setup_script(odir=out_dir, togdict=tog_dict, ncase=num_case, type='hitmid')

    # Done
    print(LOG, LOG_DELIM)
    print(LOG, "We are done here, have a nice day :-)")
    print(LOG, LOG_DELIM)
    

# Entry point
if __name__ == '__main__':
    main()
