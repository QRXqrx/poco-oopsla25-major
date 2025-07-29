#!/bin/python3

import sys
import os
import pandas as pd

from commons import *

"""
Count experimented corpus, see commons commons.RAW_CORPUS_MAP.
"""


if __name__ == '__main__':
    
    if len(sys.argv) < 2: 
        print('Usage: ./script.py MAGMA_TARGETS')
        exit(0)
        
    # Parse args.
    POCO_STR = '_poco_'
    magma_target_dir = os.path.abspath(sys.argv[1])
    exp_dirs = [_ for _ in os.listdir(magma_target_dir) if POCO_STR in _]
    print(exp_dirs)
    
    # Statistics = stats.
    data = []
    data_cols = ['target', 'corpus', 'cnt']
    for dname in exp_dirs:
        corpus_type = RAW_CORPUS_MAP[dname.split(POCO_STR)[-1]]
        corpus_root = os.path.join(magma_target_dir, dname, 'corpus')
        for target in [_ for _ in os.listdir(corpus_root) if not _.startswith('.')]:
            target_dir = os.path.join(corpus_root, target)
            # Count
            cnt = len(os.listdir(target_dir))
            data.append([target, corpus_type, cnt])
    
    # Turn into df and write to local.
    df = pd.DataFrame(data, columns=data_cols)
    df['target'] = pd.Categorical(df['target'], categories=TARGETS, ordered=True)
    df['corpus'] = pd.Categorical(df['corpus'], categories=CORPRA, ordered=True)
    df = df.sort_values(['target', 'corpus'])
    print(df)
    print(df.T)
    write_df_to_local(df, magma_target_dir, 'corpus_stats')
