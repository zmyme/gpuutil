# gpuutil

A naive tool for observing gpu status and auto set visible gpu in python code.

## How to use

1. install the package.
```shell
pip install https://git.zmy.pub/zmyme/gpuutil/archive/v0.0.3.tar.gz
```

2. for observing gpu status, just input
```shell
python -m gpuutil <options>
```
when directly running ```python -m gpuutil```, you would probably get:
```text
+----+------+------+----------+----------+------+----------------+
| ID | Fan  | Temp |   Pwr    |   Freq   | Util |      Vmem      |
+----+------+------+----------+----------+------+----------------+
| 0  | 22 % | 21 C |  9.11 W  | 300 MHz  | 0 %  | 3089/11019 MiB |
| 1  | 22 % | 23 C |  6.28 W  | 300 MHz  | 0 %  | 786/11019 MiB  |
| 2  | 38 % | 59 C | 92.04 W  | 1890 MHz | 6 %  | 3608/11019 MiB |
| 3  | 40 % | 67 C | 246.38 W | 1740 MHz | 93 % | 3598/11019 MiB |
+----+------+------+----------+----------+------+----------------+
|                          Process Info                          |
+----------------------------------------------------------------+
| [26107|0] user1(737 MiB) python                                |
| [34033|0,1] user2(1566 MiB) python                             |
| [37190|0] user2(783 MiB) python                                |
| [37260|0] user2(783 MiB) python                                |
| [30356|2] user3(3605 MiB) python train.py --args --some really |
| long arguments                                                 |
| [34922|3] user3(3595 MiB) python train.py --args --some really |
| long arguments version 2                                       |
+----------------------------------------------------------------+
```
To get more information, run ```python -m gpuutil -h```, you would get:
```text
usage: __main__.py [-h] [--profile PROFILE] [--cols COLS] [--style STYLE]
                   [--show-process SHOW_PROCESS] [--vertical VERTICAL] [--save]

optional arguments:
  -h, --help            show this help message and exit
  --profile PROFILE, -p PROFILE
                        profile keyword, corresponding configuration are saved in ~/.gpuutil.conf
  --cols COLS, -c COLS  colums to show.(Availabel cols: ['ID', 'Fan', 'Temp', 'TempMax', 'Pwr',
                        'PwrMax', 'Freq', 'FreqMax', 'Util', 'Vmem', 'UsedMem', 'TotalMem', 'FreeMem',
                        'Users']
  --style STYLE, -sty STYLE
                        column style, format: |c|l:15|r|c:14rl:13|, c,l,r are align methods, | is line
                        and :(int) are width limit.
  --show-process SHOW_PROCESS, -sp SHOW_PROCESS
                        whether show process or not
  --vertical VERTICAL, -v VERTICAL
                        whether show each user in different lines. (show user vertically)
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
