import os
import sys
import shutil
from random import sample
from tqdm import tqdm

from sampsize import cal_sample_size

"""
Given a set of N seed files, repeat sampling n seed files, build target directory 
under the given root directory and copy the sampled seed files into a target 
directory.
"""


def build_seed_set_pattern(_num: int) -> str:
    _cnt = 0
    while _num:
        _num = int(_num / 10)
        _cnt += 1
    return f'%0{_cnt}d'


if __name__ == '__main__':
    if len(sys.argv) != 4 and len(sys.argv) != 5:
        print(f'Usage: {os.path.basename(__file__)} <REPEAT_N> <SEED_DIR> <OUTPUT_ROOT_DIR> [SAMPLE_SIZE]')
        exit(0)
    repeat_n = int(sys.argv[1])
    seeds_dir = os.path.abspath(sys.argv[2])        # Input
    output_root_dir = os.path.abspath(sys.argv[3])  # Outputs

    print('repeat_n', repeat_n)
    print('seeds_dir', seeds_dir)
    print('output_root_dir', output_root_dir)
    
    # Rebuild sample dir
    if os.path.exists(output_root_dir):
        shutil.rmtree(output_root_dir)
        print('[LOG] Remove existing output_root_dir')
    os.mkdir(output_root_dir)

    # Get seed set dir pattern
    pat = build_seed_set_pattern(repeat_n)

    # Decide sample size
    seed_files = sorted([_ for _ in os.listdir(seeds_dir) if not _.startswith('.')])
    if len(sys.argv) == 4:
        sample_size = cal_sample_size(N=len(seed_files))
    else:
        sample_size = int(sys.argv[4])
        print('[LOG] Use given sample_size.')
    print('[LOG]', f'population_size {len(seed_files)}, sample_size {sample_size}')

    # Prepare sample log dir
    samp_log_dir = os.path.join(output_root_dir, 'samp_log')
    os.mkdir(samp_log_dir)

    # Sample seed files
    for i in range(repeat_n):
        idx = i + 1
        samp_name = pat % idx
        print(f'[LOG] Sample seeds for No.{samp_name} seed set...')

        # Sample randomly
        sampled_seeds = sample(seed_files, sample_size)

        # Write sample log
        samp_log_path = os.path.join(samp_log_dir, f'samp-{samp_name}')
        with open(samp_log_path, 'w') as f:
            f.write('\n'.join(sampled_seeds))
        print(f'[LOG] Write to sample log: `{samp_log_path}`')

        # Build each seed set dir
        # each_seed_set = os.path.join(output_root_dir, str(idx))
        each_seed_set = os.path.join(output_root_dir, samp_name)
        os.mkdir(each_seed_set)

        # Copy files to output dir
        for sfile in tqdm(sampled_seeds, desc='[LOG] Copy sampled seed files'):
            spath = os.path.join(seeds_dir, sfile)
            shutil.copy(spath, each_seed_set)

        print(f'[LOG] Finish copying sampled seeds to `{each_seed_set}`')
        print('[LOG] --------------------------------------')
    print('[LOG] Finish all :-)')
