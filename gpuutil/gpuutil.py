from io import StringIO
from sys import platform
import xml.etree.ElementTree as ET
import os
import json
import random
import sys
import csv
import platform

osname = platform.system()


def xml2dict(node):
    node_dict = {}
    childs = list(node)
    if len(childs) == 0:
        return node.text.strip()
    for child in childs:
        if child.tag not in node_dict:
            node_dict[child.tag] = xml2dict(child)
        else:
            if type(node_dict[child.tag]) is not list:
                node_dict[child.tag] = [node_dict[child.tag]]
            node_dict[child.tag].append(xml2dict(child))
    return node_dict

def parse_nvsmi_info(command='nvidia-smi -q -x'):
    pipe = os.popen(command)
    xml = pipe.read()
    tree = ET.fromstring(xml)
    return xml2dict(tree)

def parse_gpu_info(stat):
    # the gpu stat is a dict from parsed info.
    name = stat['product_name']
    uuid = stat['uuid']
    pci_bus_id = stat['pci']['pci_bus_id']
    fan_speed = stat['fan_speed']
    memory = stat['fb_memory_usage']
    utilization = stat['utilization']
    temperature = stat['temperature']
    power = stat['power_readings']
    clocks = stat['clocks']
    max_clocks = stat['max_clocks']
    processes = [] if 'process_info' not in stat['processes'] else stat['processes']['process_info']
    processes = processes if type(processes) is list else [processes]
    return {
        "name": name,
        "uuid": uuid,
        "pci_bus_id": pci_bus_id,
        "fan_speed": fan_speed,
        "memory": memory,
        "utilization": utilization,
        "temperature": temperature,
        "power": power,
        "clocks": clocks,
        "max_clocks": max_clocks,
        "processes": processes
    }

def simplify_gpu_info(stat):
    info = {
        "name": stat['name'],
        "memory": stat['memory'],
        "fan_speed": stat['fan_speed'],
        "utilization": stat['utilization']['gpu_util'],
        "temperature": {
            "current": stat['temperature']['gpu_temp'],
            "max": stat['temperature']['gpu_temp_max_gpu_threshold'],
        },
        "power": {
            "current": stat['power']['power_draw'],
            "max": stat['power']['default_power_limit']
        },
        "clocks": {
            "current": stat['clocks']['sm_clock'],
            "max": stat['max_clocks']['sm_clock']
        },
        "processes": [
            {
                "pid": p['pid'],
                "name": p['process_name'],
                "vmem": p['used_memory']
            } for p in stat["processes"]
        ]
    }
    return info

def short_gpu_info(stat, disp_type='brief'):
    stat_disp = {
        "id": stat['id'],
        "fan": stat['fan_speed'].split(' ')[0].strip(),
        "temp": '{cur}/{max} C'.format(
            cur = stat['temperature']['current'].split(' ')[0].strip(),
            max = stat['temperature']['max'].split(' ')[0].strip()
        ),
        "power": '{cur}/{max} W'.format(
            cur = stat['power']['current'].split(' ')[0].strip(),
            max = stat['power']['max'].split(' ')[0].strip()
        ),
        "clock": '{cur}/{max} MHz'.format(
            cur = stat['clocks']['current'].split(' ')[0].strip(),
            max = stat['clocks']['max'].split(' ')[0].strip()
        ),
        "util": stat['utilization'],
        "mem": '{cur}/{max} MiB({free}MiB free)'.format(
            cur = stat['memory']['used'].split(' ')[0].strip(),
            max = stat['memory']['total'].split(' ')[0].strip(),
            free = stat['memory']['free'].split(' ')[0].strip(),
        )
    }
    process_fmt = '{user}({vmem}MiB,pid={pid})'
    process_info = ','.join([process_fmt.format(
        user = proc['user'],
        vmem = proc['vmem'].split(' ')[0].strip(),
        pid = proc['pid']
    ) for proc in stat['processes']])
    info = ''
    if disp_type == 'detail':
        fmt = '[{id}] F:{fan}|T:{temp}|P:{power}|C:{clock}|U:{util}|M:{mem}'
        info = fmt.format(**stat_disp)
    elif disp_type == 'brief':
        fmt_short = '[{id}] Utils: {util} | Mem: {mem}'
        info = fmt_short.format(
            id=stat_disp['id'],
            util=stat_disp['util'],
            mem=stat_disp['mem']
        )

    if len(process_info) > 0:
        info += '  '
        info += process_info
    return info


def get_basic_process_info_linux():
    pipe = os.popen('ps axo user:20,pid,args:1024')
    output = pipe.read()
    lines = output.split('\n')[1:]
    processes = {}
    for line in lines:
        words = [p for p in line.split(' ') if p != '']
        if len(words) < 3:
            continue
        username = words[0]
        pid = words[1]
        command = ' '.join(words[2:])
        processes[pid] = {
            "user": username,
            "command": command
        }
    return processes

def get_basic_process_info_windows():
    pipe = os.popen("tasklist /FO CSV")
    content = StringIO(pipe.read())
    reader = csv.reader(content, delimiter=',', quotechar='"')
    content = []
    for row in reader:
        content.append(list(row))
    processes = {}
    for line in content[1:]:
        name, pid, _, _, _ = line
        processes[pid] = {
            "user": None,
            "command": name
        }
    return processes

def draw_table(table, rowsty=None, colsty=None, colsz = None):
    def justify(s, align, width):
        if align == 'c':
            s = s.center(width)
        elif align == 'r':
            s = s.rjust(width)
        elif align == 'l':
            s = s.ljust(width)
        return s

    num_cols = len(table[0])
    if rowsty is None:
        rowsty = '|' + '|'.join(['c']*len(table)) + '|'
    if colsty is None:
        colsty = '|' + '|'.join(['c']*num_cols) + '|'
    # check tables.
    for row in table:
        if len(row) != num_cols:
            raise ValueError('different cols!')
    col_width = [0] * num_cols
    if colsz is None:
        colsz = [None] * num_cols
    
    # collect widths.
    for row in table:
        for i, col in enumerate(row):
            col = str(col)
            width = max([len(c) for c in col.split('\n')])
            if colsz[i] is not None and colsz[i] < width:
                width = colsz[i]
            if width > col_width[i]:
                col_width[i] = width
    # prepare vline.
    vline = []
    colaligns = []
    col_pos = 0
    line_delemeter = '-'
    content_delemeter = ' '
    for ch in colsty:
        if ch == '|':
            vline.append('+')
        elif ch in ['c', 'l', 'r']:
            colaligns.append(ch)
            vline.append('-' * col_width[col_pos])
            col_pos += 1
    vline = line_delemeter.join(vline)
    table_to_draw = []
    row_pos = 0
    for ch in rowsty:
        if ch == '|':
            table_to_draw.append("vline")
        elif ch in ['c', 'l', 'r']:
            table_to_draw.append(table[row_pos])
            row_pos += 1;
    strings = []
    for row in table_to_draw:
        if type(row) is str:
            strings.append(vline)
            continue
        new_row = []
        max_cols = 1
        for word, align, width in zip(row, colaligns, col_width):
            cols = []
            lines = word.split('\n')
            for line in lines:
                while len(line) > 0:
                    cols.append(line[:width])
                    line = line[width:]
            cols = [justify(col, align, width) for col in cols]
            if len(cols) > max_cols:
                max_cols = len(cols)
            new_row.append(cols)
        for cols, width in zip(new_row, col_width):
            empty = ' ' * width
            while len(cols) < max_cols:
                cols.append(empty)
        rows = list(zip(*new_row))
        for row in rows:
            cols_to_drawn = []
            col_pos = 0
            for ch in colsty:
                if ch == '|':
                    cols_to_drawn.append('|')
                elif ch in ['c', 'r', 'l']:
                    cols_to_drawn.append(row[col_pos])
                    col_pos += 1
            strings.append(content_delemeter.join(cols_to_drawn))
    return '\n'.join(strings)

class GPUStat():
    def __init__(self):
        self.gpus = []
        self.raw_info = None
        self.detailed_info = None
        self.process_info = None
        self.simplified_info = None
        self.cuda_version = ''
        self.attached_gpus = ''
        self.driver_version = ''
    def get_process_info(self):
        if osname == 'Windows':
            return get_basic_process_info_windows()
        elif osname == 'Linux':
            return get_basic_process_info_linux()
    def parse(self):
        self.raw_info = parse_nvsmi_info('nvidia-smi -q -x')
        self.detailed_info = {}
        for key, value in self.raw_info.items():
            if key != 'gpu':
                self.detailed_info[key] = value
            else:
                if type(value) is not list:
                    value = [value]
                self.detailed_info[key] = [parse_gpu_info(info) for info in value]
        self.process_info = self.get_process_info()
        self.simplified_info = {}
        for key in self.detailed_info:
            if key != "gpu":
                self.simplified_info[key] = self.detailed_info[key]
            else:
                self.simplified_info[key] = [simplify_gpu_info(stat) for stat in self.detailed_info["gpu"]]
        self.cuda_version = self.simplified_info["cuda_version"]
        self.driver_version = self.simplified_info["driver_version"]
        self.attached_gpus = self.simplified_info["attached_gpus"]
        self.gpus = []
        for i, gpu in enumerate(self.simplified_info["gpus"]):
            for process in gpu['processes']:
               process.update(self.process_info[process['pid']])
            gpu['id'] = i
            self.gpus.append(gpu)

    def show(self, enabled_cols = ['ID', 'Fan', 'Temp', 'Pwr', 'Freq', 'Util', 'Vmem', 'Users'], colsty=None, colsz=None, show_command=True, vertical=False):
        self.parse()
        gpu_infos = []
        # stats = {
        #     "id": stat['id'],
        #     "fan": stat['fan_speed'].split(' ')[0].strip(),
        #     "temp_cur":  stat['temperature']['current'].split(' ')[0].strip(),
        #     "temp_max":  stat['temperature']['max'].split(' ')[0].strip(),
        #     "power_cur": stat['power']['current'].split(' ')[0].strip(),
        #     "power_max": stat['power']['max'].split(' ')[0].strip(),
        #     "clock_cur": stat['clocks']['current'].split(' ')[0].strip(),
        #     "clock_max": stat['clocks']['max'].split(' ')[0].strip(),
        #     "util":      stat['utilization'],
        #     "mem_used":  stat['memory']['used'].split(' ')[0].strip(),
        #     "mem_total": stat['memory']['total'].split(' ')[0].strip(),
        #     "mem_free":  stat['memory']['free'].split(' ')[0].strip()
        # }
        for gpu in self.gpus:
            # process_fmt = '{user}({pid})'
            # process_info = ','.join([process_fmt.format(
            #     user = proc['user'],
            #     pid = proc['pid']
            # ) for proc in gpu['processes']])
            process_fmt = '{user}({pids})'
            users_process = {}
            for proc in gpu['processes']:
                user = proc['user']
                pid = proc['pid']
                if user not in users_process:
                    users_process[user] = []
                users_process[user].append(pid)
            delemeter = ','
            if vertical:
                delemeter = '\n'
            process_info = delemeter.join(process_fmt.format(user=user, pids = '|'.join(users_process[user])) for user in users_process)
            info_gpu = {
                'ID': '{0}'.format(str(gpu['id'])),
                'Fan': '{0} %'.format(gpu['fan_speed'].split(' ')[0].strip()),
                'Temp': '{0} C'.format(gpu['temperature']['current'].split(' ')[0].strip()),
                'TempMax': '{0} C'.format(gpu['temperature']['max'].split(' ')[0].strip()),
                'Pwr': '{0} W'.format(gpu['power']['current'].split(' ')[0].strip()),
                'PwrMax': '{0} W'.format(gpu['power']['max'].split(' ')[0].strip()),
                'Freq': '{0} MHz'.format(gpu['clocks']['current'].split(' ')[0].strip()),
                'FreqMax': '{0} MHz'.format(gpu['clocks']['max'].split(' ')[0].strip()),
                'Util': '{0} %'.format(gpu['utilization'].split(' ')[0]),
                'Vmem': '{0}/{1} MiB'.format(
                    gpu['memory']['used'].split(' ')[0].strip(),
                    gpu['memory']['total'].split(' ')[0].strip(),
                ),
                'UsedMem': '{0} MiB'.format(gpu['memory']['used'].split(' ')[0].strip()),
                'TotalMem': '{0} MiB'.format(gpu['memory']['total'].split(' ')[0].strip()),
                'FreeMem': '{0} MiB'.format(gpu['memory']['free'].split(' ')[0].strip()),
                'Users': process_info
            }
            gpu_infos.append(info_gpu)
        align_methods = {key:'r' for key in gpu_infos[0]}
        align_methods['Users'] = 'l'
        if enabled_cols is None:
            enabled_cols = list(align_methods.keys())
        c_align = [align_methods[col] for col in enabled_cols]
        info_table = [enabled_cols]
        for info in gpu_infos:
            this_row = [info[key] for key in enabled_cols]
            info_table.append(this_row)
        info = draw_table(info_table, rowsty='|c|{0}|'.format('c'*(len(info_table)-1)), colsty=colsty, colsz=colsz) + '\n'
        if show_command:
            procs = {}
            for gpu in self.gpus:
                for proc in gpu['processes']:
                    pid = proc['pid']
                    proc['gpu'] = [str(gpu['id'])]
                    if type(proc['vmem']) is str:
                        proc['vmem'] = int(proc['vmem'].split(' ')[0])
                    if pid not in procs:
                        procs[pid] = proc
                    else:
                        procs[pid]['gpu'].append(str(gpu['id']))
                        procs[pid]['vmem'] += proc['vmem']
            proc_fmt = '[{pid}|{gpus}] {user}({vmem} MiB) {cmd}'
            proc_strs = []
            for pid in procs:
                this_proc_str = proc_fmt.format(
                    user = procs[pid]['user'],
                    vmem = procs[pid]['vmem'],
                    pid = procs[pid]['pid'].rjust(5),
                    cmd = procs[pid]['command'],
                    gpus = ','.join(procs[pid]['gpu'])
                )
                proc_strs.append(this_proc_str)
            proc_info = '\n'.join(proc_strs)
            table_width = info.find('\n')
            proc_info = draw_table([['Process Info'.center(table_width-4)], [proc_info]], rowsty="c|c|", colsty="|l|", colsz=[table_width-4])
            info += proc_info
        print(info)

class MoreGPUNeededError(Exception):
    def __init__(self):
        pass

def set_gpu(gpus, show=False):
    gpus = [str(i) for i in gpus]
    gpus.sort()
    gpus = ','.join(gpus)
    if show:
        print('using gpu:', gpus)
    os.environ['CUDA_VISIBLE_DEVICES'] = gpus

def choose_interface(values, default=None, hint=None, max_try = 3, case_sensitive=False):
    if default is None:
        default = values[0]
    failed_num = 0
    if not case_sensitive:
        values = [v.lower() for v in values]
    if hint is not None:
        print(hint)
    while failed_num < max_try:
        choosed = input('>>> ').lower()
        if choosed in values:
            return choosed
        else:
            print('Invalid choice!')
        failed_num += 1
    return default

def ask_use_non_empty_gpu(stat, empty, non_empty):
    really_used_gpu = []
    print('No enough free gpu, would you love to use these following non-empty gpu?')
    for gpu in non_empty:
        print(short_gpu_info(stat.gpus[gpu], disp_type='detail'))
    hint = 'Y: Use the non-empty gpu\nN: Exit\nM: set gpu mannuly'
    action = choose_interface(['y', 'n', 'm'], default='n', hint=hint, case_sensitive=False)
    if action == 'y':
        really_used_gpu = empty + non_empty
    elif action == 'n':
        raise MoreGPUNeededError
    elif action == 'm':
        gpu_strs = input('Please input the gpu you want to use (use comma as delemeter)\n>>> ')
        really_used_gpu = [x.strip() for x in gpu_strs.split(',')]
        really_used_gpu = [int(x) for x in really_used_gpu if x != '']
    return really_used_gpu

def auto_set(num, allow_nonfree=True, ask=True, blacklist=[], show=True):
    stat = GPUStat()
    stat.parse()
    if num > len(stat.gpus) - len(blacklist):
        raise MoreGPUNeededError
    gpus = {int(gpu['id']):int(gpu['memory']['free'].split(' ')[0].strip()) for gpu in stat.gpus}
    gpus = {key:value for key, value in gpus.items() if key not in blacklist}
    free_gpus = [int(gpu['id']) for gpu in stat.gpus if len(gpu['processes']) == 0]
    free_gpus = [x for x in free_gpus if x not in blacklist]
    selected_gpu = []
    if num <= len(free_gpus):
        # random select num gpu from all free_gpus.
        random.shuffle(free_gpus)
        selected_gpu = free_gpus[:num]
    elif allow_nonfree:
        # find the gpu with most memory.
        nonfree_gpus = [[key,value] for key, value in gpus.items() if key not in free_gpus]
        nonfree_gpus.sort(key=lambda x:x[1], reverse=True)
        nonfree_gpus = [x[0] for x in nonfree_gpus]
        print('nonfree_gpus:', nonfree_gpus)
        num_remeaning = num - len(free_gpus)
        nonfree_gpus_used = nonfree_gpus[:num_remeaning]
        print('nonfree_gpus_used:', nonfree_gpus_used)
        if not ask:
            selected_gpu = free_gpus + nonfree_gpus_used
        else:
            selected_gpu = ask_use_non_empty_gpu(stat, free_gpus, nonfree_gpus_used)
    else:
        raise MoreGPUNeededError
    set_gpu(selected_gpu, show=show)

if __name__ == '__main__':
    print(get_basic_process_info_windows())