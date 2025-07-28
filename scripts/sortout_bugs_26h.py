#!/usr/bin/env python3

import os
import sys
import random
import json
import pandas as pd

from upsetplot import UpSet, from_indicators
import matplotlib
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Times New Roman'
# plt.rcParams['font.family'] = 'Georgia'
# plt.rcParams['font.family'] = 'Libertine'

# To avoid type-3 font error
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
plt.rcParams['font.size'] = 18

# exp conf
TIME_LIMIT = 86400
K = 10  # number of trials 
N = 20  # number of repeats

colors = {
    'sndfile_fuzzer':            '#1f77b4',  # blue
    'xmllint':                   '#ff7f0e',  # orange
    'libxml2_xml_read_memory_fuzzer': '#2ca02c',  # green
    'sqlite3_fuzz':              '#d62728',  # red
    'lua':                       '#9467bd',  # purple
    'libpng_read_fuzzer':        '#8c564b',  # brown
    'tiffcp':                    '#e377c2',  # pink
    'tiff_read_rgba_fuzzer':    '#7f7f7f',  # gray
}

TARGETS = list(colors.keys())
TARGET_ID_MAP = {val: f'T0{idx+1}' for idx, val in enumerate(TARGETS)}
CORPORA = ['all', 'optimin', 'cmin', 
           'cminplus-2h', 'cminplus', 
           'poco-2h', 'poco',
           'cmin_delta', 'cmin_26h']

H26 = 93600
H24 = 86400
time_delta = {
    'sndfile_fuzzer': H24 + 54,            
    'xmllint': H24 + 897,                 
    'libxml2_xml_read_memory_fuzzer': H24 + 28,
    'sqlite3_fuzz': H24 + 6550,              
    'lua': H24 + 2902,                      
    'libpng_read_fuzzer': H24 + 1067,    
    'tiffcp': H24 + 2172,               
    'tiff_read_rgba_fuzzer':H24 + 6501, 
}

def venn_bugs(rdata, cols, figpath):
    bug_sets = []
    for i in range(5):  
        bugs = set(rdata.loc[i, "bugs"].split(";"))
        bug_sets.append(bugs)
    venn5(bug_sets, set_labels=cols)
    plt.savefig(figpath)
    print('[LOG] Output to:', figpath)


def read_json_as_dict(jsonpath):
    with open(jsonpath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data
       

def extract_R_data(bugdf, cols):
    data = []
    data_cols = ['corpus', 'bugs']
    for corpus in cols:
        cdf = bugdf[['target', 'bug', corpus]][bugdf[corpus] != '---']
        bugs = cdf['target'] + '-' + cdf['bug']
        data.append([corpus, ';'.join(list(bugs))])
    return pd.DataFrame(data, columns=data_cols)

def convert(cell):
    if isinstance(cell, str) and '---' in cell:
        return False
    return True

corpus_map = {
    'all': 'ALL',
    'optimin': 'OptiMin',
    'cmin': 'Cmin',
    'cminplus-2h': 'Cmin+',
    'cminplus': 'Cmin+(A)',
    'poco-2h': 'PoCo',
    'poco': 'PoCo(A)',
    'cmin_delta': 'Cmin(δ)',
    'cmin_26h': 'Cmin(26h)',
}

def depict_upset_plot(columns, bugdata: pd.DataFrame, figpath):
    figdf = bugdata.copy()[['target', 'bug'] + columns]
    # Rename to the names for showing.
    figdf = figdf.rename(columns=corpus_map)
    columns = [corpus_map[_] for _ in columns]
    figdf[columns] = figdf[columns].applymap(convert)
    # Ensure every bug has a finder.
    figdf = figdf[figdf[columns].any(axis=1)]   
    data = from_indicators(columns, figdf[columns])
    # Draw data
    upset = UpSet(data, subset_size='count', show_counts='%d')
    upset.plot()
    plt.savefig(figpath)
    print('[LOG] Output to:', figpath)


def bug_shorten(bug) -> str:
    bug_map = {
        'PNG0': 'P',
        'XML0': 'X',
        'LUA0': 'L',
        'SND0': 'S',
        'SQL0': 'Q',
        'TIF0': 'F',
    }
    for k, v in bug_map.items():
        if k in bug:
            return bug.replace(k, v)

def craft_cmin_delta(df26: pd.DataFrame) -> pd.DataFrame:
    df = df26.copy()
    df['max_time'] = df['target'].map(time_delta)
    df = df[df['time'] < df['max_time']]
    return df.drop(columns=['max_time'])

def process_bug_df(data_24h_dir, data_26h_dir):
    # Merge new bug data with 1. cmin 26h data; and 2. others data.
    # cmin_26h
    bug_csv = os.path.join(data_26h_dir, 'bug-all.csv')
    cmin_26h = pd.read_csv(bug_csv, index_col=0)
    cmin_26h = cmin_26h[(cmin_26h['corpus'] == 'cmin') &
                        (cmin_26h['time'] <= H26)]
    cmin_24h = cmin_26h.copy()
    cmin_24h = cmin_24h[(cmin_24h['time'] <= H24)]  
    # cmin_delta
    cmin_delta = craft_cmin_delta(cmin_26h)
    # rename
    cmin_delta['corpus'] = 'cmin_delta'
    cmin_26h['corpus'] = 'cmin_26h'
    # print(cmin_26h, cmin_24h, cmin_delta)
    
    # Merge first
    bug_df = pd.concat([cmin_24h, cmin_26h, cmin_delta])
    
    # Get other 24h bug data.
    bug_csv = os.path.join(data_24h_dir, 'bug-all.csv')
    other_24h = pd.read_csv(bug_csv, index_col=0)
    other_24h = other_24h[(other_24h['corpus'] != 'cmin') & 
                          (other_24h['time'] < H24)]
    # print(other_24h, other_24h['time'].max())
    
    # Merge again
    return pd.concat([bug_df, other_24h])

def process_trial_json(data_24h_dir, data_26h_dir):
    
    # Process 26h json: Only keep cmin trials.
    trial_json = os.path.join(data_26h_dir, 'bug-trials.json')
    cmin_map = read_json_as_dict(trial_json)
    
    # Process 24 json: remove cmin part.
    trial_json = os.path.join(data_24h_dir, 'bug-trials.json')
    res = read_json_as_dict(trial_json)
    del res['cmin']
    
    res['cmin'] = cmin_map['cmin']
    return res

def filter_df_no_time(orig_df: pd.DataFrame, 
                      trialmap: dict, k: int) -> pd.DataFrame:
    _df = orig_df.copy()
    # Sample k randomly for each pair of (corpus, target)
    _grps = _df.groupby(['corpus', 'target'])
    _samp_dfs = []
    # Handle cmin trials specially.
    cmin_trial_map = {}
    for (corpus, target), _grp in _grps:
        corkey = 'cmin' if (corpus.startswith('cmin_')) else corpus
        _trials = trialmap[corkey][target]
        if len(_trials) < k:
            raise ValueError(f'No {k} trials for ({corpus}, {target}), we only have {len(_trials)}')
        if corkey == 'cmin':
            if not target in cmin_trial_map:
                cmin_trial_map[target] = random.sample(list(_trials), k)
            _trials = cmin_trial_map[target]
            # print('!!! Use old cmin trials')
        else:
            _trials = random.sample(list(_trials), k)
        # print(corpus, target, len(_trials))
        _samp_df = _grp[_grp['trial'].isin(_trials)]
        _samp_dfs.append(_samp_df) 
    return pd.concat(_samp_dfs)


def main():
    if len(sys.argv) < 3: 
        print('Usage: ./script.py DATA_24h_DIR DATA_26h_DIR')
        exit(0)
    
    # Read in args
    data_24h_dir = os.path.abspath(sys.argv[1])
    data_26h_dir = os.path.abspath(sys.argv[2])
    
    # Get bug data
    bug_data = process_bug_df(data_24h_dir, data_26h_dir)
    # print(bug_data)
    # print(bug_data['corpus'].unique())
    
    # Get trial map
    trial_map = process_trial_json(data_24h_dir, data_26h_dir)
    # print(trial_map.keys()) 
        
    # Debug
    # df = filter_df_no_time(bug_data, trial_map, K)
    # for cor in df['corpus'].unique():
    #     for target in TARGETS:
    #         ddf = df[(df['corpus'] == cor) & (df['target'] == target)]
    #         print(cor, target, len(ddf['trial'].unique()))
    
    # Ok, now we are ready for sortout.
    
    res_dir = os.path.join(data_26h_dir, '_bugs')
    if not os.path.isdir(res_dir):
        os.makedirs(res_dir)
    
    for i in range(N):
        
        cnt_str = str(i+1).zfill(2)
        
        # Output the df
        df = filter_df_no_time(bug_data, trialmap=trial_map, k=K)
        print(df)
        csv_name = os.path.join(res_dir, f'bug-{TIME_LIMIT}-{cnt_str}.csv')
        df.to_csv(csv_name)
        print('[LOG] Output to:', csv_name)
        
        # Parse detailed data and output.
        for btype in df['type'].unique():
            data = []
            # for target in df['target'].unique():
            for target in TARGETS:
                for bug in sorted(df['bug'].unique()):
                    bdata = df[(df['type'] == btype) & 
                               (df['target'] == target) & 
                               (df['bug'] == bug)]
                    if bdata.empty:
                        continue
                    # Shorten the bug
                    row_data = [target, bug_shorten(bug)]
                    for corpus in df['corpus'].unique():
                        cdata = bdata[(bdata['corpus'] == corpus)]
                        median = cdata['time'].median()
                        succ = len(cdata['trial'].unique()) / K
                        if succ > 1:
                            print(cdata)
                            raise ValueError(f'succ should not > 1 ({succ})', )
                        if pd.isna(median):
                            row_data.append('---')
                        else:
                            row_data.append('%d \\tiny{(%.1f)}' % (round(median), succ))
                    data.append(row_data)
            columns = ['target', 'bug'] + df['corpus'].unique().tolist()
            
            #  Output detailed bug stats
            res_df = pd.DataFrame(data, columns=columns)
            re_cols = ['target', 'bug'] + CORPORA
            res_df = res_df[re_cols]
            csv_name = os.path.join(res_dir, f'bug-{btype}-{TIME_LIMIT}-{cnt_str}.csv')
            res_df.to_csv(csv_name)
            print('[LOG] Output to:', csv_name)
            
            # Upset figures
            # Fig 5d, 24h 
            cols = ['all', 'optimin', 'cmin', 'cminplus', 'poco', 'cmin_delta', 'cmin_26h']
            fig_path = os.path.join(res_dir, f'bug-{btype}-{TIME_LIMIT}-{cnt_str}-r5d.pdf')
            depict_upset_plot(cols, res_df, fig_path)
            # Fig 2h, 24h
            cols = ['all', 'optimin', 'cmin', 'cminplus-2h', 'poco-2h', 'cmin_delta', 'cmin_26h']
            fig_path = os.path.join(res_dir, f'bug-{btype}-{TIME_LIMIT}-{cnt_str}-r2h.pdf')
            depict_upset_plot(cols, res_df, fig_path)
    
    
                    
if __name__ == '__main__':
    main()
    