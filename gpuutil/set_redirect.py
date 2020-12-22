import argparse
import os
import json

availabel_name_trans = ['cmd', 'user', 'pid']

parser = argparse.ArgumentParser()
parser.add_argument('--nvsmi', '-nv', default=None, type=str, help='a file indicates real nvidia-smi -q -x output.')
parser.add_argument('--ps', '-ps', default=None, type=str, help='a file indicates real ps-like output.')
parser.add_argument('--ps_name_trans', '-pst', default=None, type=str, help='a dict of name trans, \
                                                                            format: name1=buildin,name2=buildin, \
                                                                            buildin can be choosen from {0}'.format(','.join(availabel_name_trans)))

args = parser.parse_args()

# lets chech the pst.
parsed_name_trans = {}
name_trans = args.ps_name_trans
if name_trans is not None:
    name_trans = name_trans.split(',')
    name_trans = [t.strip() for t in name_trans]
    name_trans = [t for t in name_trans if t!='']
    for item in name_trans:
        item = item.split('=', maxsplit=1)
        if len(item) != 2:
            raise ValueError('there must be a = in nametrans')
        key, value = item
        if value not in avaliable_name_trans:
            raise ValueError('given buildin name {0} do not exist, avaliable: {1}'.format(value, ','.join(availabel_name_trans)))
        parsed_name_trans[key] = value

config_file = os.path.expanduser('~/.gpuutil.conf')
configuration = {}
if os.path.isfile(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        configuration = json.load(f)
configuration['redirect'] = {
    "nvsmi_src": args.nvsmi,
    "ps_src": args.ps,
    "ps_name_trans": parsed_name_trans
}

with open(config_file, 'w+', encoding='utf-8') as f:
    f.write(json.dumps(configuration, ensure_ascii=False, indent=4))