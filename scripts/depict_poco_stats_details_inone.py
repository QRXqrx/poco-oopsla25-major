#!/usr/bin/env python3

import os
import sys
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Times New Roman'
# plt.rcParams['font.family'] = 'Georgia'
# plt.rcParams['font.family'] = 'Libertine'

# To avoid type-3 font error
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
plt.rcParams['font.size'] = 18

FIGSIZE = (8, 5)
ALPHA = 0.7

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

PLATEAU_TARGETS = ['sndfile_fuzzer', 'xmllint', 'sqlite3_fuzz']
TARGETS = list(colors.keys())
TARGET_ID_MAP = {val: f'T0{idx+1}' for idx, val in enumerate(TARGETS)}
TIME_UPPER = 432000

def main():
  
  if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <cnts_path> <out_dir>")
    print("  <cnts_path>  Path to the input file or directory")
    print("  <out_dir>    Path to the output figures")
    sys.exit(1)
  
  cnts_path = os.path.abspath(sys.argv[1])
  time_upper = TIME_UPPER / 3600
  
  out_dir = os.path.abspath(sys.argv[2])
  out_dir = os.path.join(out_dir, '_results', 'figs-poco-stats')
  os.makedirs(out_dir, exist_ok=True)
  
  print(TARGET_ID_MAP)
  
  fig, ax = plt.subplots(figsize=FIGSIZE)
  alpha = ALPHA
  # Create canvas
  plt.gca().set_facecolor('#f0f0f0')
  plt.grid(True, linestyle='-', linewidth=1, color='white')
  
  # All the target in one table.
  for target in TARGETS:
    print(target)
    # Locate cnts csvs.
    csv_path = os.path.join(cnts_path, target, 'seed_cnts.csv')
    df = pd.read_csv(csv_path)[['rel_time', 'seed_cnt', 'seed_cnt_wo_dedup']]
    # Turn time into hours
    df['rel_time'] = df['rel_time'] / 3600    
    # Add timeupper point
    last_ratio = df['seed_cnt'].iloc[-1]
    last_ratio_nodedup = df['seed_cnt_wo_dedup'].iloc[-1]
    df.loc[len(df)] = [time_upper, last_ratio, last_ratio_nodedup]    
    df['cnt_ratio'] = df['seed_cnt'] / df['seed_cnt_wo_dedup'] * 100
    
    # Find the final seed_cnt_wo_dedup, to exclude 0 ones.
    last_ratio = df['cnt_ratio'].iloc[-1]
    # first_idx = df[df['cnt_ratio'] == last_ratio].index[0]
    # first_idx_time = df.iloc[first_idx]['rel_time']
    
    # Plot existed data
    lwid = 2
    color = colors[target]
    ax.plot(df['rel_time'], df['cnt_ratio'], label=TARGET_ID_MAP[target], 
            linestyle='-', color=color, linewidth=lwid, alpha=alpha, 
            markevery=range(len(df) - 1), marker='o', ms=4.5)
    # df_truncated = df.iloc[:first_idx+1]
    # ax.plot(df_truncated['rel_time'], df_truncated['cnt_ratio'], 
    #         label=TARGET_ID_MAP[target], linestyle='-', color=color, 
    #         linewidth=lwid, alpha=alpha, marker='o')
    # # plt.scatter([first_idx_time], [last_ratio+1], color=color, marker='v', s=40, alpha=alpha)
    # if first_idx_time < time_upper:
    #   plt.plot([first_idx_time, time_upper], [last_ratio, last_ratio], linestyle='-.', color=color, linewidth=lwid, alpha=alpha)

    # Labels and legends
    # ax.set_xlabel('rel_time')
    # ax.set_ylabel('seed count')
    # ax.set_xticklabels([])  
    # ax.set_yticklabels([])  
    # ax.legend()
    
    # Remove ticks
    # ax.tick_params(axis='both', which='both', length=0) 
    
  # Remove borders
  for spine in ax.spines.values():
    spine.set_visible(False)
  
  # To output
  ax.set_xlabel('PoCo Time (Hours)')
  ax.set_ylabel('Fresh Seed (%)')
  # xticks = [0, 40, 80, 120]
  xticks = [0, 20, 40, 60, 80, 100, 120]
  xticklabs = [str(_) for _ in xticks]
  plt.xticks(xticks, xticklabs)
  # plt.yticks([0, 50, 100], ['0', '50', '100'])
  # plt.legend(loc='upper center', bbox_to_anchor=(0.48, 1.25),
  #          ncol=4, 
  #         #  fancybox=True, 
  #         #  shadow=True, 
  #         frameon=False, 
  #          fontsize=12)
  # ax.legend()
  # plt.legend(loc='upper right')
  plt.tight_layout()
  # plt.show()
  figpath = os.path.join(out_dir, f'cnt-ratios.pdf')
  fig.savefig(figpath)
  print('[LOG] Output to:', figpath)
    

if __name__ == '__main__':
  main()
