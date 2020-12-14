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

# style format: |c|l:15|r|c:14rl:13|
def parse_style(style):
    components = []
    limits = []
    while len(style) > 0:
        ch = style[0]
        if ch == '|':
            components.append(ch)
            style = style[1:]
            continue
        elif ch in ['l', 'r', 'c']:
            limit = None
            style = style[1:]
            if style[0] == ':':
                style = style[1:]
                digits = ''
                while style[0].isdigit():
                    digits += style[0]
                    style = style[1:]
                if digits != '':
                    limit = int(digits)
            components.append(ch)
            limits.append(limit)
    style = ''.join(components)
    return style, limits

if __name__ == '__main__':
    stat = GPUStat()

    avaliable_cols = ['ID', 'Fan', 'Temp', 'TempMax', 'Pwr', 'PwrMax', 'Freq', 'FreqMax', 'Util', 'Vmem', 'UsedMem', 'TotalMem', 'FreeMem', 'Users']
    recommended_cols = ['ID', 'Fan', 'Temp', 'Pwr', 'Freq', 'Util', 'Vmem']

    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', '-p', default=None, type=str, help='profile keyword, corresponding configuration are saved in ~/.gpuutil.conf')
    parser.add_argument('--cols', '-c', type=csv2list, help='colums to show')
    parser.add_argument('--style', '-sty', type=parse_style, help='column style')
    parser.add_argument('--show-process', '-sp', default=True, type=str2bool, help='whether show process or not')
    parser.add_argument('--save', default=False, action="store_true", help='save config to profile')
    args = parser.parse_args()
    cols = args.cols if args.cols is not None else recommended_cols
    show_process = args.show_process
    style, limit = args.style
    unexpected_cols = []
    for col in cols:
        if col not in avaliable_cols:
            unexpected_cols.append(col)
    if len(unexpected_cols) > 0:
        raise ValueError('Unexpected cols {0} occured. Cols must be chosen from {1}'.format(unexpected_cols, ','.join(avaliable_cols)))

    if args.save:
        params = {
            "cols": cols,
            "show-process": show_process,
            "style": style,
            "limit": limit
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
            style = None
            limit = None
            if "style" in params:
                style = params["style"]
            if "limit" in params:
                limit = params["limit"]

        else:
            raise ValueError('Profile do not exist.\nAvaliable Profiles:{0}'.format(','.join(list(config.keys()))))
    stat.show(enabled_cols = cols, colsty=style, colsz=limit, show_command=show_process)