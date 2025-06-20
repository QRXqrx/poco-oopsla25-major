import os
import sys


def read_last_time(pd_path: str) -> int:
    with open(pd_path, 'r') as f:
        # relative_time, cycles_done, cur_item...
        _last_line = f.readlines()[-1]
        return int(_last_line.split(', ')[0])


if __name__ == '__main__':
    # Parse arguments
    if len(sys.argv) != 2:
        print('Usage: <THIS_SCRIPT> <OUTS_DIR>')
        exit(0)
    outs_dir = os.path.abspath(sys.argv[1])

    # Count crashing campaign
    crash_cnt = 0
    non_crash_cnt = 0
    crash_time = 0
    max_crash_time = -1
    min_crash_time = 86401
    for fn in sorted(os.listdir(outs_dir)):
        # Locate crashes dir
        out_dir = os.path.join(outs_dir, fn, 'default')
        crashes_dir = os.path.join(out_dir, 'crashes')
        if len(os.listdir(crashes_dir)) == 0:
            # No crash found, skip
            non_crash_cnt += 1
            continue
        # Parse time to find the bug. Read the last line of plot_data and get time.
        plot_data = os.path.join(out_dir, 'plot_data')
        time = read_last_time(pd_path=plot_data)
        max_crash_time = max(max_crash_time, time)
        min_crash_time = min(min_crash_time, time)
        crash_time += time
        crash_cnt += 1

    # Print result
    seed = os.path.basename(outs_dir)
    print(f'seed {seed}')
    print(f'bug_find_ratio {crash_cnt}/{crash_cnt+non_crash_cnt}')
    if crash_cnt != 0:
        print(f'ave_crash_time {crash_time/crash_cnt}(s)')
    print(f'min_crash_time {min_crash_time}(s)')
    print(f'max_crash_time {max_crash_time}(s)')
