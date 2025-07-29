#!/usr/bin/env python3

import os
import sys
import json
import string
import secrets

from collections import defaultdict

from commons import *

def bugjson2df(jsonpath, trialmap: dict) -> pd.DataFrame:
    data = []
    print(jsonpath)
    bug_dict = load_json_as_dict(jsonpath)['results'][AFLPP]
    for corpus_fullname, v0 in bug_dict.items():
        for target, v1 in v0.items():
            for trial, v2 in v1.items():
                for bugtype, v3 in v2.items():
                    for bugid, time in v3.items():
                        corpus = parse_corpus(corpus_fullname)
                        trial_hash = trialmap[corpus][target][trial]
                        data.append([trial_hash, corpus, target, 
                                     bugid, bugtype, time])
    columns = ['trial', 'corpus', 'target', 'bug', 'type', 'time']
    return pd.DataFrame(data=data, columns=columns)

# def locate_ball_tars(dirpath: str):
#     balls = []
#     for dirpath, dirnames, filenames in os.walk(dirpath):
#         # Speed up!
#         dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
#         for filename in filenames:
#             if filename == 'ball.tar':
#                 full_path = os.path.join(dirpath, filename)
#                 # print(full_path)
#                 balls.append(full_path)
#     return balls

def parse_ball(ballstr:str):
    # /ar/aflplusplus/lua_poco_poco/lua/6/ball.tar
    parts = ballstr.split('/')
    # corpus, target, trial
    return parse_corpus(parts[3]), parts[4], parts[5]


EXCLUDE_DIRS = ['cache', 'lock', 'log', 'poc', 'tmp', 'findings', 'monitor', 'deprecate']
def main():
    if len(sys.argv) < 2: 
        print('Usage: ./script.py BUGDATA_DIR')
        exit(0)
    
    # Prepare vars
    bugdata_dir = os.path.abspath(sys.argv[1])
    
    # Parse into rows of stats.
    bugdf_list = []
    # Record all seen trial hashes.
    glob_trial_map = defaultdict(lambda: defaultdict(list))
    for subdir in os.listdir(bugdata_dir):
        bugs_dir = os.path.join(bugdata_dir, subdir)
        bugs_json = os.path.join(bugs_dir, 'bugs.json')
        if subdir.startswith('.') or not os.path.isdir(bugs_dir):
            continue
        if not os.path.exists(bugs_json):
            continue
        ball_tars = locate_files(bugs_dir, 'ball.tar', EXCLUDE_DIRS)
        # Locate trials.
        trial_map = defaultdict(lambda: defaultdict(dict))
        for ball in ball_tars:
            corpus, target, trial = parse_ball(ball.replace(bugs_dir, ''))
            if trial in trial_map[corpus][target]:
                raise ValueError(f'Duplicated trial for: {ball}')
            trial_hash = generate_unique_id()
            trial_map[corpus][target][trial] = trial_hash
            glob_trial_map[corpus][target].append(trial_hash)
        trial_map = to_dict(trial_map)
        print(trial_map)
        # fuzzer, project, target, trial, reached/triggered, bugid: time.
        bug_df = bugjson2df(bugs_json, trial_map)
        bugdf_list.append(bug_df)
        print('------------------------------------------')
    glob_trial_map = to_dict(glob_trial_map)
    # print(glob_trial_map)
    for corpus, targets in glob_trial_map.items():
        for target, trials in targets.items():
            print(corpus, target, len(trials))
    
    # Merge dfs and write to local.
    df = pd.concat(bugdf_list)
    write_df_to_local(df, bugdata_dir, 'bug-all')
    write_as_json(os.path.join(bugdata_dir, 'bug-trials.json'), glob_trial_map)

if __name__ == '__main__':
    main()
    