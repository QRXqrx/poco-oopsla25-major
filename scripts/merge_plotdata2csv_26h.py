#!/usr/bin/env python3

import os
import sys
import numpy as np

from collections import defaultdict

from commons import *

"""
Special analyses on 26hour and 24+delta results.
"""

TIME_BASE = 86400
time_delta = {
    'sndfile_fuzzer': TIME_BASE + 54,            
    'xmllint': TIME_BASE + 897,                 
    'libxml2_xml_read_memory_fuzzer': TIME_BASE + 28,
    'sqlite3_fuzz': TIME_BASE + 6550,              
    'lua': TIME_BASE + 2902,                      
    'libpng_read_fuzzer': TIME_BASE + 1067,    
    'tiffcp': TIME_BASE + 2172,               
    'tiff_read_rgba_fuzzer':TIME_BASE + 6501, 
}

def parse_plot_data(pdstr:str):
    # /ar/aflplusplus/lua_poco_poco/lua/6/findings/default/plot_data
    parts = pdstr.split('/')
    # corpus, target, trial
    return parse_corpus(parts[3]), parts[4], parts[5]


def pd2edges(pd_path, delta_time):
    """
    Only read edges at (1) 26hour and (2) 24hour + delta
    """
    TIME_26h = 93600
    pddf = pd.read_csv(pd_path, delimiter=', ', engine='python')[["# relative_time", "edges_found"]]
    pddf = pddf.rename(columns={"# relative_time": "time"})
    edges_26h = pddf[pddf['time'] <= TIME_26h]['edges_found'].max()
    edges_delta = pddf[pddf['time'] <= delta_time]['edges_found'].max()
    return edges_delta, edges_26h

EXCLUDE_DIRS = ['cache', 'lock', 'log', 'poc', 'tmp', 'monitor', 
                'queue', 'crashes', 'hangs', 'deprecate']
def main():
    if len(sys.argv) < 2: 
        print('Usage: ./script.py RESULT_DIR')
        exit(0)
    
    # Prepare vars
    result_dir = os.path.abspath(sys.argv[1])
    
    # Record all seen trial hashes.
    cols = ['corpus', 'target', 'trial', 'edges_delta', 'edges_26h']
    data = []
    for subdir in os.listdir(result_dir):
        fuzzdata_dir = os.path.join(result_dir, subdir)
        if subdir.startswith('.') or not os.path.isdir(fuzzdata_dir):
            continue
        plot_data_li = locate_files(fuzzdata_dir, 'plot_data', EXCLUDE_DIRS)
        for plot_data in plot_data_li:
            corpus, target, _ = parse_plot_data(plot_data.replace(fuzzdata_dir, ''))
            if corpus != 'cmin':
                continue
            edelta, e26h = pd2edges(plot_data, time_delta[target])
            trial = generate_unique_id()
            print(corpus, target, trial, edelta, e26h)
            data.append([corpus, target, trial, edelta, e26h])
    df = pd.DataFrame(data, columns=cols)
    print(df)
    
    write_df_to_local(df, result_dir, 'cov-all-26h')

if __name__ == '__main__':
    main()
    