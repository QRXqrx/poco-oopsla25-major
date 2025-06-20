import sys
import os

"""
Check whether cmin results are consistent.
"""


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print(f"Usage: python3 {os.path.basename(__file__)} <cmin_dir1> <cmin_dir2>")
        exit(0)

    # Parse arg
    cmin_dir1 = os.path.abspath(sys.argv[1])
    cmin_dir2 = os.path.abspath(sys.argv[2])

    # Turn in to set
    cmin_set1 = set(os.listdir(cmin_dir1))
    cmin_set2 = set(os.listdir(cmin_dir2))

    # print(cmin_set1)
    # print(cmin_set2)
    # Compute diff
    diff_set = (cmin_set1 - cmin_set2) | (cmin_set2 - cmin_set1)

    print('[LOG]', f'len1 {len(cmin_set1)}, len2 {len(cmin_set2)}')
    print('[LOG]', 'diff_len ', len(diff_set))
    print('[LOG]', 'diff_set ', diff_set)
