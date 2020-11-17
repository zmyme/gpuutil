from gpuutil import GPUStat
import sys
import json
import argparse
import os

def csv2list(csv):
    l = [col.strip() for col in csv.split(',')]
    return [col for col in l if col != '']
def str2bool(s):
    if s.lower() in ['t', 'yes', 'y', 'aye', 'positive', 'true']:
        return True
    else:
        return False

def load_config():
    home_dir = os.path.expanduser('~')
    configpath = os.path.join(home_dir, '.gpuutil.conf')
    if not os.path.isfile(configpath):
        return {}
    with open(configpath, 'r', encoding='utf-8') as f:
        return json.load(f)
def save_config(config):
    home_dir = os.path.expanduser('~')
    configdir = os.path.join(home_dir, '.gpuutil.conf')
    with open(configdir, 'w+', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    stat = GPUStat()

    avaliable_cols = ['ID', 'Fan', 'Temp', 'TempMax', 'Pwr', 'PwrMax', 'Freq', 'FreqMax', 'Util', 'Vmem', 'UsedMem', 'TotalMem', 'FreeMem', 'Users']
    recommended_cols = ['ID', 'Fan', 'Temp', 'Pwr', 'Freq', 'Util', 'Vmem']

    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', '-p', default=None, type=str, help='profile keyword, corresponding configuration are saved in ~/.gpuutil.conf')
    parser.add_argument('--cols', '-c', type=csv2list, help='colums to show')
    parser.add_argument('--show-process', '-sp', default=True, type=str2bool, help='whether show process or not')
    parser.add_argument('--save', default=False, action="store_true", help='save config to profile')
    args = parser.parse_args()
    cols = args.cols if args.cols is not None else recommended_cols
    show_process = args.show_process
    unexpected_cols = []
    for col in cols:
        if col not in avaliable_cols:
            unexpected_cols.append(col)
    if len(unexpected_cols) > 0:
        raise ValueError('Unexpected cols {0} occured. Cols must be chosen from {1}'.format(unexpected_cols, ','.join(avaliable_cols)))

    if args.save:
        params = {
            "cols": cols,
            "show-process": show_process
        }
        profile = args.profile if args.profile is not None else input('Please input your profile name:\n>>> ')
        config = load_config()
        config[profile] = params
        save_config(config)
    elif args.profile is not None:
        config = load_config()
        if args.profile in config:
            params = config[args.profile]
            cols = params["cols"]
            show_process = params["show-process"]
        else:
            raise ValueError('Profile do not exist.\nAvaliable Profiles:{0}'.format(','.join(list(config.keys()))))
    stat.show(enabled_cols = cols, show_command=show_process)