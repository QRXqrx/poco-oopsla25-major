#!/usr/bin/env python3

import os
import sys
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from depict_poco_stats_details_inone import colors, TARGETS, TARGET_ID_MAP, FIGSIZE, ALPHA

plt.rcParams['font.family'] = 'Times New Roman'
# plt.rcParams['font.family'] = 'Georgia'
# plt.rcParams['font.family'] = 'Libertine'

# To avoid type-3 font error
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
plt.rcParams['font.size'] = 24

TIME_UPPER = 86400

def depict_time_component(df:pd.DataFrame, figpath: str):
  
  # Limit in the time upper.
  df = df.copy()
  df = df[df['sum_cost'] < TIME_UPPER]
  df = df.drop(columns=['turn', 'opened_tog'])
  
  # Get the last line and turn into percentages
  final_composition = df.iloc[-1]
  final_composition = final_composition / final_composition['sum_cost']
  # print((final_composition['cmin'] + final_composition['crash_tog']) * 100)
  # print(final_composition.to_numpy())
  
  # Prepare fig data.
  data = final_composition[['cmin']]
  data['crash_reck'] = final_composition['crash_tog'] + final_composition['crash_tog_exec']
  data['other'] = final_composition.drop(['cmin', 'crash_tog', 'crash_tog_exec','sum_cost']).sum()
  
  # Compo in pie
  color_map = {
    "cmin": "#1f77b4",       
    "crash_reck": "#ff7f0e", 
    "other": "#7f7f7f",      
  }
  colors = list(color_map.values())
  plt.figure(figsize=(4,4))
  plt.pie(
      data, 
      colors=colors,
      # labels=data.index, 
      autopct=lambda p: f'{p:.1f}%' if p > 5 else '',  # 只显示大于1%的占比
      startangle=90
  )
  # plt.title("Time Composition by Stage")
  plt.tight_layout()
  # plt.show()
  plt.savefig(figpath)
  print('[LOG] Output to:', figpath)
  return final_composition.to_numpy().tolist()


def sci_formatter(y, _):
    return f'{y:.1e}'

def depict_disabled_togs(data, figpath):
  
  plt.rcParams['font.size'] = 18
  
  fig, ax = plt.subplots(figsize=FIGSIZE)
  alpha = ALPHA
  # Create canvas
  plt.gca().set_facecolor('#f0f0f0')
  plt.grid(True, linestyle='-', linewidth=1, color='white')
  
  # All the target in one table.
  for target, togdata in data:
    df = togdata.copy()
    last_tog = togdata['opened_tog'].iloc[-1]
    df.loc[len(togdata)] = [TIME_UPPER, last_tog]
    df['rel_time'] = df['sum_cost'] / 3600
    df['tog_ratio'] = df['opened_tog'] / df['opened_tog'].max() * 100
    # print(df, target)
    
    # Plot existed data
    lwid = 2
    color = colors[target]
    # ax.plot(df['rel_time'], df['tog_ratio'], label=TARGET_ID_MAP[target], 
    #         linestyle='-', color=color, linewidth=lwid, alpha=alpha, 
    #         markevery=range(len(df) - 1), marker='o', ms=4.5)
    ax.plot(df['rel_time'], df['opened_tog'], label=TARGET_ID_MAP[target], 
            linestyle='-', color=color, linewidth=lwid, alpha=alpha, 
            markevery=range(len(df) - 1), marker='o', ms=4.5)

    # Remove borders
  for spine in ax.spines.values():
    spine.set_visible(False)
  
  # To output
  ax.set_xlabel('PoCo Time (Hours)')
  ax.set_ylabel('# of Disabled Guards')
  # ax.yaxis.set_major_formatter(FuncFormatter(sci_formatter))
  # xticks = [0, 8, 16, 24]
  xticks = [0, 4, 8, 12, 16, 20, 24]
  xticklabs = [str(_) for _ in xticks]
  plt.xticks(xticks, xticklabs)
  # plt.yticks([5000, 10000, 15000, 20000, 25000, 30000], 
  #            ['5000', '10000', '15000', '20000', '25000', '30000'])
  plt.yticks([5000, 10000, 15000, 20000, 25000, 30000], 
             ['5k', '10k', '15k', '20k', '25k', '30k'])
  # plt.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
  # ax.legend()
  # plt.legend(loc='upper right')
  plt.tight_layout()
  # plt.show()
  fig.savefig(figpath)
  print('[LOG] Output to:', figpath)

def main():
  
  if len(sys.argv) < 2: 
    print('Usage: ./script.py TIME_LOG_DIR')
    exit(0)
  
  time_csv_folder = os.path.abspath(sys.argv[1])
  
  out_dir = os.path.join(time_csv_folder, '_timecompo_tognum')
  if not os.path.exists(out_dir):
    os.makedirs(out_dir, exist_ok=True)
  
  disable_togs_data = []
  compos = []
  for target in TARGETS:
    time_csv = os.path.join(time_csv_folder, target, 'log.csv')
    timecompo_fig = os.path.join(out_dir, f'{TARGET_ID_MAP[target]}-{target}.pdf')
    df = pd.read_csv(time_csv)
    compo = [target] + depict_time_component(df, timecompo_fig)
    print(compo)
    compos.append(compo)
    # Gather data of disbaled toggles.
    disable_togs_data.append((target, df[['sum_cost', 'opened_tog']]))
  
  # Record time csv.
  compo_df = pd.DataFrame(data=compos, 
                          columns=['target', 'parse_hierarchy', 'sort_guards',
                                   'run_cmin', 'revoke', 'crash_iden', 'crash_exec',
                                   'conv_handle', 'obstacle_handle', 'total'])
  print(compo_df)
  compo_df.to_csv('./time-compo.csv')
  
  # Depict toggles line
  togs_fig = os.path.join(out_dir, f'trend-toggles.pdf')
  depict_disabled_togs(disable_togs_data, togs_fig) 
 
if __name__ == '__main__':
  main()
