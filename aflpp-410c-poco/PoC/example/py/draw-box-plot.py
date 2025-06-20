import os
import sys
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind


# Tp avoid type 3 font error
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42


def read_last_time(pd_path: str) -> int:
    with open(pd_path, 'r') as f:
        # relative_time, cycles_done, cur_item...
        _last_line = f.readlines()[-1]
        return int(_last_line.split(', ')[0])


if __name__ == '__main__':
    # Parse arguments
    if len(sys.argv) != 2:
        print('Usage: <THIS_SCRIPT> <BOX_OUTS_ROOT>')
        exit(0)
    box_outs_dir = os.path.abspath(sys.argv[1])

    # Collecting finishing time.
    data_dict = dict()
    for sn in sorted(os.listdir(box_outs_dir)):
        # Skip .DS_Store
        if sn.startswith('.') or sn.endswith('.pdf'):
            continue
        print(f'Process {sn} ...')
        # seed_name = '\"%s\"' % sn.split('-')[-1]
        # seed_name = sn.split('-')[-1]
        sn_splices = sn.split('-')
        seed_name = f'{sn_splices[1]}(s{sn_splices[0]})'
        outs_dir = os.path.join(box_outs_dir, sn)
        # Sanitize for each campaign. Everybody should crash :-).
        data_dict[seed_name] = []
        for fn in sorted(os.listdir(outs_dir)):
            # Skip .DS_Store
            if fn.startswith('.'):
                continue
            # Locate crashes dir
            out_dir = os.path.join(outs_dir, fn, 'default')
            crashes_dir = os.path.join(out_dir, 'crashes')
            if len(os.listdir(crashes_dir)) == 0:
                raise RuntimeError(f'Find a non-crashing campaign for {sn}! Kick it out!')
            # Parse time to find the bug. Read the last line of plot_data and get time.
            plot_data = os.path.join(out_dir, 'plot_data')
            time = read_last_time(pd_path=plot_data)
            # Collect into corresponding time row
            data_dict[seed_name].append(time)

    # Turn into data frame
    df = pd.DataFrame(data=data_dict, columns=list(data_dict.keys()))
    # print(df)
    # Draw boxplot
    # plt.rcParams['font.size'] = 16
    plt.rcParams['font.size'] = 20
    # fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(4, 9))
    # fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(9, 4))
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(20, 4))
    # fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(12, 4))
    boxprops = dict(linestyle='-', linewidth=3, color='black')
    medianprops = dict(linestyle='-', linewidth=1, color='black')
    bplot = ax.boxplot(df,
                       # vertical/horizon box alignment
                       vert=False,
                       # fill the box with color
                       # patch_artist=True,
                       labels=df.columns,   # will be used to label x-ticks
                       # Box style
                       # boxprops=boxprops,
                       # Median line
                       medianprops=medianprops,
                       )

    # ax.set_title('Rectangular box plot')
    # ax.set(xlabel='Crash Time (s)', xticks=[1000*_ for _ in range(13)])
    # ax.set(xlabel='Crash Time (s)', xticks=[500*_ for _ in range(28)])
    ax.grid(color='gray', linestyle='--', linewidth=0.5)
    # ax.set(ylabel='Crash Time (s)')
    fig.tight_layout()
    # plt.show()
    fig_path = os.path.join(box_outs_dir, 'hello-seeds-boxplot.pdf')
    fig.savefig(fig_path)
    print(f'Output to {fig_path}')

    # T-test
    print('Compute t-test values...')
    for s1 in df.columns:
        for s2 in df.columns:
            if s1 == s2:
                continue
            print(f'`{s1}` and `{s2}`, {ttest_ind(df[s1], df[s2])}')

