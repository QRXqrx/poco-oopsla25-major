#!/usr/bin/env python3

import os
import sys
import numpy as np

from collections import defaultdict

from commons import *


# def locate_plot_data(dirpath: str):
#     pds = []
#     for dirpath, dirnames, filenames in os.walk(dirpath):
#         # Speed up!
#         dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
#         for filename in filenames:
#             if filename == 'plot_data':
#                 full_path = os.path.join(dirpath, filename)
#                 # print(full_path)
#                 pds.append(full_path)
#     return pds

def parse_plot_data(pdstr:str):
    # /ar/aflplusplus/lua_poco_poco/lua/6/findings/default/plot_data
    parts = pdstr.split('/')
    # corpus, target, trial
    return parse_corpus(parts[3]), parts[4], parts[5]


def pd2df(pd_path):
    # TIME_LIMIT = 86400
    # TIME_LIMIT = 172800
    TIME_LIMIT = 93600
    TIME_GAP = 900
    pddf = pd.read_csv(pd_path, delimiter=', ', engine='python')[["# relative_time", "edges_found"]]
    pddf = pddf.rename(columns={"# relative_time": "time"})
    pddf = pddf[pddf["time"] <= TIME_LIMIT]
    # Sample every GAP
    time_points = np.arange(0, TIME_LIMIT+1, TIME_GAP)
    samp_data = [{"time": 0, "edges_found": pddf.iloc[0]["edges_found"]}]
    for t in time_points[1:]:
        eligible = pddf[pddf["time"] <= t]
        if not eligible.empty:
            nearest_row = eligible.iloc[-1]
            samp_data.append({"time": t, "edges_found": nearest_row["edges_found"]})
    # pddf = pd.DataFrame(samp_data)
    # print(pddf)
    return pd.DataFrame(samp_data)

EXCLUDE_DIRS = ['cache', 'lock', 'log', 'poc', 'tmp', 'monitor', 
                'queue', 'crashes', 'hangs', 'deprecate']
def main():
    if len(sys.argv) < 2: 
        print('Usage: ./script.py RESULT_DIR')
        exit(0)
    
    # Prepare vars
    result_dir = os.path.abspath(sys.argv[1])
    
    # Parse into rows of stats.
    df_list = []
    # Record all seen trial hashes.
    glob_trial_map = defaultdict(lambda: defaultdict(list))
    for subdir in os.listdir(result_dir):
        fuzzdata_dir = os.path.join(result_dir, subdir)
        if subdir.startswith('.') or not os.path.isdir(fuzzdata_dir):
            continue
        plot_data_li = locate_files(fuzzdata_dir, 'plot_data', EXCLUDE_DIRS)
        # print(plot_data_li)
        # Locate trials.
        trial_map = defaultdict(lambda: defaultdict(dict))
        for plot_data in plot_data_li:
            corpus, target, trial = parse_plot_data(plot_data.replace(fuzzdata_dir, ''))
            if trial in trial_map[corpus][target]:
                raise ValueError(f'Duplicated trial for: {plot_data}')
            trial_hash = generate_unique_id()
            trial_map[corpus][target][trial] = trial_hash
            glob_trial_map[corpus][target].append(trial_hash)
            # Parse plot_data into csv
            df = pd2df(plot_data)
            df['trial'] = trial_hash
            df['corpus'] = corpus
            df['target'] = target
            df['cov_rate'] = df['edges_found'] / TOTAL_EDGE_MAP[target]
            df = df[['corpus', 'target', 'trial',
                     'time','edges_found', 'cov_rate']]
            df_list.append(df)
            print(df)
            if type(df) == str:
                raise Exception()
        trial_map = to_dict(trial_map)
        print(fuzzdata_dir)
        print(trial_map)
        print('------------------------------------------')
    glob_trial_map = to_dict(glob_trial_map)
    # print(glob_trial_map)
    for corpus, targets in glob_trial_map.items():
        for target, trials in targets.items():
            print(corpus, target, len(trials))
    # Merge dfs and write to local.
    df = pd.concat(df_list)
    write_df_to_local(df, result_dir, 'cov-all')
    write_as_json(os.path.join(result_dir, 'cov-trials.json'), glob_trial_map)
    

if __name__ == '__main__':
    main()
    