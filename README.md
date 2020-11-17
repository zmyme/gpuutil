# gpuutil

A naive tool for observing gpu status and auto set visible gpu in python code.

## How to use

1. install the package.
```shell
pip install https://git.zmy.pub/zmyme/gpuutil/archive/v0.0.2.tar.gz
```

2. for observing gpu status, just input
```shell
python -m gpuutil <options>
```
when directly running ```python -m gpuutil```, you would probably get:
```text
+---+------+------+---------+---------+------+---------------+
|ID | Fan  | Temp |   Pwr   |   Freq  | Util |      Vmem     |
+---+------+------+---------+---------+------+---------------+
| 0 | 22 % | 33 C |  4.47 W | 300 MHz |  0 % | 1569/11019 MiB|
| 1 | 22 % | 35 C |  3.87 W | 300 MHz |  0 % |    3/11019 MiB|
| 2 | 22 % | 36 C |  8.22 W | 300 MHz |  0 % |    3/11019 MiB|
| 3 | 22 % | 36 C | 21.82 W | 300 MHz |  0 % |    3/11019 MiB|
+---+------+------+---------+---------+------+---------------+
[34860|0] user1(783 MiB) python train.py --some -args
[38694|0] user2(783 MiB) python train.py --some --other -args
```
To get more information, run ```python -m gpuutil -h```, you would get:
```text
python __main__.py -h 
usage: __main__.py [-h] [--profile PROFILE] [--cols COLS] [--show-process SHOW_PROCESS] [--save]

optional arguments:
  -h, --help            show this help message and exit
  --profile PROFILE, -p PROFILE
                        profile keyword, corresponding configuration are saved in ~/.gpuutil.conf
  --cols COLS, -c COLS  colums to show
  --show-process SHOW_PROCESS, -sp SHOW_PROCESS
                        whether show process or not
  --save                save config to profile
```

3. To auto set visible gpu in your python code, just use the following python code.
```python
from gpuutil import auto_set
auto_set(1)
```

the ```auto_set```function is defined as follows:
```python
# num: the number of the gpu you want to use.
# allow_nonfree: whether use non-empty gpu when there is no enough of them.
# ask: if is set to true, the script will ask for a confirmation when using non empty gpu. if false, it will use the non empty gpu directly.
# blacklist: a list of int, the gpu in this list will not be used unless you mannuly choose them.
# show: if set to true, it will show which gpu is currently using.
def auto_set(num, allow_nonfree=True, ask=True, blacklist=[], show=True):
	# some code here.
```

## ps:
1. you can get more detailed gpu info via accessing gpuutil.GPUStat class, for more information, just look the code.
2. Since it use ps command to get detailed process info, it can only be used on linux.
