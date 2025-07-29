#!/bin/python3 

import os
import sys
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

from commons import *

"""
Locate trial root folder, and run showmap_batch.sh in parallel
"""

WORKERS = 25

def locate_mg_trial_root(raw_dir: str) -> list: 
    _dirs = []
    for _fn1 in os.listdir(raw_dir):
        _expid_dir = os.path.join(raw_dir, _fn1)
        if not os.path.isdir(_expid_dir) or _fn1.startswith('_'):
            continue
        if _fn1 == 'tmp':
            continue
        _fuzzer_dir = os.path.join(_expid_dir, 'ar', AFLPP)
        for _fn2 in os.listdir(_fuzzer_dir):
            if not '_poco_' in _fn2:
                continue
            _corpus_dir = os.path.join(_fuzzer_dir, _fn2)
            for _fn3 in os.listdir(_corpus_dir):
                if _fn3 not in TARGETS:
                    continue
                _dirs.append(os.path.join(_corpus_dir, _fn3))
    return sorted(_dirs)   


def parse_info_from_path(tr_path: str) -> tuple:
    _cols = tr_path.split('/')
    return _cols[-2].split('_poco_')[-1], _cols[-1]  # Corpus, Target   


def run_showmap_task(tdir, corpus, target, out_dir, showmap_batch, showmap, target_dir):
    os.makedirs(out_dir, exist_ok=True)
    print(f'[LOG][{corpus}/{target}] Running showmap batch → {out_dir}')
    process = subprocess.Popen(
        ['bash', showmap_batch, tdir, out_dir, showmap, target_dir, target],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        text=True
    )
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f'[{corpus}/{target}] {output.strip()}')
    return process.returncode

if __name__ == '__main__':
    
    if len(sys.argv) < 5: 
        print('Usage: ./script.py SHOWMAP SHOWMAP_BATCH_SH TARGET_DIR RAWDATA_DIR')
        exit(0)
    
    showmap = os.path.abspath(sys.argv[1])
    showmap_batch = os.path.abspath(sys.argv[2])
    target_dir = os.path.abspath(sys.argv[3])
    raw_dir = os.path.abspath(sys.argv[4])
    out_root = os.path.join(raw_dir, '_showmap')
    
    if os.path.exists(out_root):
        shutil.rmtree(out_root)
        print('[LOG] Del outdated:', out_root)
    os.mkdir(out_root)
    print('[LOG] Create:', out_root)
    
    trialroot_dirs = locate_mg_trial_root(raw_dir)
    print(f"[LOG] Found {len(trialroot_dirs)} trial root dirs.")
    
    # Collect tasks
    tasks = []
    for tdir in trialroot_dirs:
        corpus, target = parse_info_from_path(tdir)
        if corpus not in ['poco_2h', 'poco', 'cmin', 'cminplus_2h', 'cminplus']:
            continue
        out_dir = os.path.join(out_root, target, corpus, generate_unique_id())
        tasks.append((tdir, corpus, target, out_dir, showmap_batch, showmap, target_dir))
    
    # Run tasks in parallel (max 25 at a time)
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(run_showmap_task, *task) for task in tasks]
        for future in as_completed(futures):
            code = future.result()
            print(f'[LOG] Task completed with return code {code}')
