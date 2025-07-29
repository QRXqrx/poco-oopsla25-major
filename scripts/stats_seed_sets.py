#!/bin/python3 

import os
import sys
import pandas as pd

from commons import TARGETS

SET_NAMES = [
    'corpus', 'cmin', 'poco', 'poco-2h', 'optimin',
    'cminplus', 'cminplus-2h']


if __name__ == '__main__':
    
    if len(sys.argv) < 2: 
        print('Usage: ./script.py SEET_ROOT')
        exit(0)
    seed_root = os.path.abspath(sys.argv[1])
    
    data = []
    for trgt in TARGETS:
        row_data = [trgt]
        for setname in SET_NAMES:
            trgtdir = os.path.join(seed_root, setname, trgt)
            seed_files = set([_ for _ in os.listdir(trgtdir) if not _.startswith('.')])
            seed_cnt = len(seed_files)
            row_data.append(seed_cnt)
        data.append(row_data)
    # Write to df.
    cols = ['trgt'] + SET_NAMES
    df = pd.DataFrame(data=data, columns=cols)
    print(df)
    df.to_csv('./set_stats.csv')
        