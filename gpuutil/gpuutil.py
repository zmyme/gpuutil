import xml.etree.ElementTree as ET
import os
import json
import random
import sys


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

def get_basic_process_info():
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
        self.process_info = get_basic_process_info()
        self.simplified_info = {
            "driver_version": self.detailed_info["driver_version"],
            "cuda_version": self.detailed_info["cuda_version"],
            "attached_gpus": self.detailed_info["attached_gpus"],
            "gpus": [simplify_gpu_info(stat) for stat in self.detailed_info["gpu"]]
        }
        self.cuda_version = self.simplified_info["cuda_version"]
        self.driver_version = self.simplified_info["driver_version"]
        self.attached_gpus = self.simplified_info["attached_gpus"]
        self.gpus = []
        for i, gpu in enumerate(self.simplified_info["gpus"]):
            for process in gpu['processes']:
               process.update(self.process_info[process['pid']])
            gpu['id'] = i
            self.gpus.append(gpu)

    def show(self, disp_type='brief', command=True):
        self.parse()
        lines = [short_gpu_info(info, disp_type=disp_type) for info in self.gpus]
        print('================== GPU INFO ==================')
        print('\n'.join(lines))
        if command:
            print('================ PROCESS INFO ================')
            procs = {}
            for gpu in self.gpus:
                for proc in gpu['processes']:
                    pid = proc['pid']
                    if pid not in procs:
                        procs[pid] = proc
            proc_fmt = '[{pid}] {user}({vmem} MiB) {cmd}'
            proc_strs = []
            for pid in procs:
                this_proc_str = proc_fmt.format(
                    user = procs[pid]['user'],
                    vmem = procs[pid]['vmem'].split(' ')[0],
                    pid = procs[pid]['pid'], 
                    cmd = procs[pid]['command']
                )
                proc_strs.append(this_proc_str)
            proc_info = '\n'.join(proc_strs)
            print(proc_info)

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
    
