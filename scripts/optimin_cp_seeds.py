#!/bin/python3

import sys
import os
import shutil
from tqdm import tqdm


if __name__ == '__main__':
    
    if len(sys.argv) < 4: 
        print('Usage: ./script.py LOG_DIR CORPUS_DIR OUT_DIR TARGET_NAME')
        exit(0)
        
    # Parse args.
    log_dir = os.path.abspath(sys.argv[1])
    corpus_dir = os.path.abspath(sys.argv[2])
    out_dir = os.path.abspath(sys.argv[3])
    target_name = sys.argv[4]
    
    # Locate optimin log.
    log_path = os.path.join(log_dir, f'{target_name}.log')
    print('[LOG] Optmin log:', log_path)
    
    # Parse log
    with open(log_path, 'r') as f:
        seed_names = [_.strip() for _ in f.readlines()[1:]]
    # print(seed_names, len(seed_names))
    
    # Create dir to cp seeds.
    optimin_corpus = os.path.join(out_dir, target_name)
    if os.path.exists(optimin_corpus):
        print('[WARN] Optimin corpus existed, quit:', optimin_corpus)
        exit(0)
    os.mkdir(optimin_corpus)
    print('[LOG] Create:', optimin_corpus)
    
    # Cp seeds.
    for seed in tqdm(seed_names, desc='[LOG] Copy seeds'):
        seed_path = os.path.join(corpus_dir, target_name, seed)
        shutil.copy(seed_path, optimin_corpus)
    print('[LOG] Finish all, thank u :-)')
