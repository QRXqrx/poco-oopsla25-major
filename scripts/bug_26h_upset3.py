#!/usr/bin/env python3

import os
import sys
import pandas as pd

from sortout_bugs_26h import depict_upset_plot

def depict_rq(rq:str, bug_csv:str, cols: list):
    df = pd.read_csv(bug_csv, index_col=0)
    fig_path = bug_csv.replace('.csv', f'-{rq}.pdf')
    depict_upset_plot(cols, df, fig_path)

def main():
    if len(sys.argv) < 2: 
        print('Usage: ./script.py BUG_CSV')
        exit(0)
    
    # Read in args
    bug_csv = os.path.abspath(sys.argv[1])
    
    # Upset figures
    # RQ2: practical
    depict_rq('rq2', bug_csv, ['all', 'optimin', 'cmin', 'cminplus-2h', 'poco-2h'])
    # RQ3: longer poco
    depict_rq('rq3', bug_csv, ['all', 'optimin', 'cmin', 'cminplus', 'poco'])
    # RQ4: poco vs. longer fuzzing
    depict_rq('rq4', bug_csv, ['all', 'poco-2h', 'cmin',  'cmin_delta', 'cmin_26h'])
    
                    
if __name__ == '__main__':
    main()
    