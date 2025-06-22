#!/bin/python3

import sys
import os
import shutil

"""
Localize seeds of all poco rnds, deduplicate, and copy them into one.
"""


if __name__ == '__main__':
    
    if len(sys.argv) < 3: 
        print('Usage: ./script.py SRC_POCO_DIR DEST_DIR')
        exit(0)
        
    # Parse args.
    src_root_dir = os.path.abspath(sys.argv[1])
    dest_dir = os.path.abspath(sys.argv[2])
    
    seed_name_set = set()
    for poco_rnd in os.listdir(src_root_dir):
        # Only consider poco rnds.
        if poco_rnd.startswith('.'):
            continue
        poco_rnd_dir = os.path.join(src_root_dir, poco_rnd)
        if not os.path.isdir(poco_rnd_dir):
            continue
        for seed_name in os.listdir(poco_rnd_dir):
            if seed_name == '.filelist.1':
                continue
            # Deduplicate.
            orig_len = len(seed_name_set)
            seed_name_set.add(seed_name)
            if len(seed_name_set) == orig_len:
                continue
            # Find a new one, just copy.
            src_path = os.path.join(poco_rnd_dir, seed_name)
            dst_path = os.path.join(dest_dir, seed_name)
            shutil.copy2(src_path, dst_path)
            print(f'[LOG] Cp from `{src_path}` to `{dst_path}`')
    print('[LOG]', '============================')
    print('[LOG]', f'Find {len(seed_name_set)} for target {os.path.basename(src_root_dir)}')
    print('[LOG]', 'Finish all :-)')
    print('[LOG]', '============================')
