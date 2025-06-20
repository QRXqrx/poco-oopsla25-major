import os
import argparse
import subprocess
import copy

from subprocess import DEVNULL
from poccshm import *


DEFAULT_MAP_SIZE = 1 << 16


def run_target_afl(target_args: list, shmid: int, 
                   stdin=None, be_quiet: bool = False, togid2on: str = None):
    _envs = {"__AFL_SHM_ID": str(shmid)}
    if togid2on:
        _envs[togid2on] = '1'
    print(LOG, 'envs', _envs)
    if be_quiet:
        subprocess.run(target_args, env=_envs, stdin=stdin, stdout=DEVNULL, stderr=DEVNULL)
    else:
        print(LOG, 'Run target_args:', target_args)
        print(LOG, '+++++++++++++++ Program Outputs +++++++++++++++ ')
        subprocess.run(target_args, env=_envs, stdin=stdin)
        print(LOG, '+++++++++++++++++++++++++++++++++++++++++++++++ ')


def execute_test_case_and_record_hitset(
        casefile: str, 
        cmd: list, 
        shmid: int, 
        togshm,
        togid2on: str = None,
        mapsize: int = DEFAULT_MAP_SIZE,
        use_stdin: bool = False) -> set:
    _hitset = set()
    # Copy cmd
    _cmd = copy.deepcopy(cmd)
    # Judge type and run.
    if use_stdin:
        # use_stdin, use file instream as input.
        with open(casefile, 'r') as _istream:
            run_target_afl(_cmd, shmid=shmid, stdin=_istream, togid2on=togid2on)
    else:
        # use_file, replace @@ with the path to the file.            
        _idx = _cmd.index(FILEIN_LOC)
        _cmd[_idx] = casefile
        run_target_afl(_cmd, shmid=shmid, togid2on=togid2on)  
    # Update hitset.
    for _i in range(1, mapsize):
        if togshm[0][_i]:
            _hitset.add(_i)
            # Clean shm
            togshm[0][_i] = 0
    return _hitset


def build_arg_parser() -> argparse.ArgumentParser:
    """
    Build command line argument parser.
    :return: Arg parser instance.
    """
    _p = argparse.ArgumentParser()
    _p.add_argument('--in_file', '-i', required=True, type=str,
                    help='Input test file.')
    _p.add_argument('--bitmap_size', '-b', required=False, type=int, default=DEFAULT_MAP_SIZE,
                    help='Directory to output toggle analysis results.')
    _p.add_argument('--tog_id', '-t', required=False, type=str, default=None,
                    help='The id of the toggle you want to disable.')
    return _p


def main():
    
    # Parse cmd.
    argv, target_cmd, use_stdin = parse_target_cmd()
    print(LOG, 'argv:', argv)
    print(LOG, 'target_cmd:', target_cmd)

    # Parse real args
    cmd_parser = build_arg_parser()
    args = cmd_parser.parse_args(argv)
    in_file = os.path.abspath(args.in_file)
    map_size = args.bitmap_size
    tog_id_str = None
    if args.tog_id:
        tog_id_str = f'{TOG_PAT}{args.tog_id}'

    # Start core logic: first run the input file, then set the tog, and then run again
    # Check whether there are any descripancies between these two runs.

    # Load lots of shm functions from C library.
    c_shmget = load_c_shmget()
    c_shmctl = load_c_shmctl()
    c_shmat = load_c_shmat()
    c_shmdt = load_c_shmdt()

    # Load a shm
    shm_id = c_shmget(IPC_PRIVATE, map_size, IPC_CREAT | IPC_EXCL | DEFAULT_PERMISSION)
    shm = load_shm(cshmat=c_shmat, shmid=shm_id, cdtype=c_uint8, shmlen=map_size)

    # Run test cases once.
    set_before = execute_test_case_and_record_hitset(casefile=in_file, cmd=target_cmd,
                                                     shmid=shm_id, togshm=shm,
                                                     mapsize=map_size, use_stdin=use_stdin)
    # Set the toggle and run again
    set_after = execute_test_case_and_record_hitset(casefile=in_file, cmd=target_cmd,
                                                    shmid=shm_id, togshm=shm, togid2on=tog_id_str,
                                                    mapsize=map_size, use_stdin=use_stdin)
    
    # Make diff
    b_a_diff = sorted(list(set_before-set_after))
    a_b_diff = sorted(list(set_after-set_before))
    print(LOG, f'hits_before, len {len(set_before)}, {sorted(list(set_before))}')
    print(LOG, f'hits_after, len {len(set_after)}, {sorted(list(set_after))}')
    print(LOG, f'before - after, len {len(b_a_diff)}, {b_a_diff}')
    print(LOG, f'after - before, len {len(a_b_diff)}, {a_b_diff}')
    


    # Free the shm
    c_shmdt(shm) 
    c_shmctl(shm_id, IPC_RMID, 0)

    

# Entry point
if __name__ == '__main__':
    main()