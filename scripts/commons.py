import os
import json
import string
import secrets
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from collections import defaultdict

# To avoid type-3 font error
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
plt.rcParams['font.size'] = 16

AFLPP = 'aflplusplus'

RAW_CORPUS_MAP = {
    'all': 'All',
    "optimin": 'Optimin',
    'cmin': 'Cmin',
    'cminplus-2h': 'Cmin+',
    'cminplus': 'Cmin+all',
    'poco-2h': 'PoCo',
    'poco': 'PoCoall'
}
RAW_CORPORA = list(RAW_CORPUS_MAP.keys())
CORPRA = list(set((RAW_CORPUS_MAP.values())))

COLORS = {
    'Cmin': "Orange",
    'PoCo': "Blue",
    'All': "Gray",
    'Cmin+': "Brown",
    'Optimin': "Green",
}

TOTAL_EDGE_MAP = {
    # libsndfile
   'sndfile_fuzzer': 19024, 
   # libxml2
   'xmllint': 67654, 
   'libxml2_xml_read_memory_fuzzer': 65044,
   # sqlite3
   'sqlite3_fuzz': 31092, 
    # libpng
   'libpng_read_fuzzer': 6703, 
   # libtiff
   'tiffcp': 12783,
   'tiff_read_rgba_fuzzer': 13271, 
   # lua
   'lua': 5921 
}
TARGETS = list(TOTAL_EDGE_MAP.keys())
# TARGETS = [
#     # openssl
#     # 'asn1parse', 'bignum',
#     # libsndfile
#     'sndfile_fuzzer',
#     # sqlite3
#     'sqlite3_fuzz',
#     # libtiff
#     'tiff_read_rgba_fuzzer',
#     # libxml2
#     'xmllint', 'xml_read_memory_fuzzer',
# ]
FUZZERS = [
  'aflplusplus'
]
# CORPRA = ['Cmin', 'PoCo']
N_REPEAT = 10

def target_map(target: str) -> str: 
    if target == 'libxml2_xml_read_memory_fuzzer':
        return 'xml_read_memory_fuzzer'
    return target


def corpus_map(raw_cname: str) -> str:
    # if raw_cname.endswith('_all'):
    #     return 'All'
    # if raw_cname.endswith('_optimin'):
    #     return 'Optimin'
    # if raw_cname.endswith('_cmin'):
    #     return 'Cmin'
    # if raw_cname.endswith('_poco'):
    #     return 'PoCo'
    # if raw_cname.endswith('_cminplus'):
    #     return 'Cmin+'
    # raise Exception('Unexpected raw_cname: ' + raw_cname)
    _suffix = raw_cname.split('_')[-1]
    return RAW_CORPUS_MAP[_suffix]


def write_df_to_local(dataframe: pd.DataFrame, csv_dir: str, csv_fn: str):
    _csv = os.path.join(csv_dir, f'{csv_fn}.csv')
    dataframe.to_csv(_csv)
    print('[LOG] Write to local:', _csv) 
    
def output_fig(figure: plt.Figure, path: str, tight: bool = True):
    if tight:
        figure.tight_layout()
    figure.savefig(path)
    print('[LOG] Output to:', path)
    plt.close()
    
def load_json_as_dict(path: str) -> dict:
    with open(path, 'r') as _jfile:
        return json.load(_jfile)

def write_as_json(path: str, dat: dict):
    with open(path, 'w', encoding='utf-8') as _jfile:
        json.dump(dat, _jfile, indent=2)
        # json.dump(dat, _jfile)
    print('[LOG] Write to local:', path)

def generate_unique_id(length=16):
    chars = string.digits + string.ascii_lowercase 
    return ''.join(secrets.choice(chars) for _ in range(length))

def parse_corpus(fullname: str) -> str:
    return '-'.join(fullname.split('_')[2:]) 


def to_dict(d):
    if isinstance(d, defaultdict):
        return {k: to_dict(v) for k, v in d.items()}
    elif isinstance(d, dict):
        return {k: to_dict(v) for k, v in d.items()}
    else:
        return d

def locate_files(dirpath: str, fn, exclude_list):
    files = []
    for dirpath, dirnames, filenames in os.walk(dirpath):
        # Speed up!
        dirnames[:] = [d for d in dirnames if d not in exclude_list]
        for filename in filenames:
            if filename == fn:
                full_path = os.path.join(dirpath, filename)
                # print(full_path)
                files.append(full_path)
    return files
