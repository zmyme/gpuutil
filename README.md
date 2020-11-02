# gpuutil

A naive tool for observing gpu status and auto set visible gpu in python code.

## How to use

1. install the package.
```
pip install https://git.zmy.pub/zmyme/gpuutil/archive/v0.0.1.tar.gz
```

2. for observing gpu status, just input
```
python -m gpuutil <options>
```
where options can either be "brief" or "detail", and you will get something like
```
================== GPU INFO ==================
[0] Utils: 94 % | Mem: 10166/11019 MiB(853MiB free)  user1(10163MiB,pid=14018)
[1] Utils: 89 % | Mem: 6690/11019 MiB(4329MiB free)  user2(6687MiB,pid=19855)
[2] Utils: 0 % | Mem: 1/11019 MiB(11018MiB free)
[3] Utils: 0 % | Mem: 1/11019 MiB(11018MiB free)
================ PROCESS INFO ================
[14018] user1(10163 MiB) python train.py --some -args
[19855] user2(6687 MiB) python train.py --some --different --args
```

3. To auto set visible gpu in your python code, just use the following python code.
```python
from gpuutil import auto_set
autoset(1)
```

the ```auto_set```function is defined as follows:
```python
# num: the number of the gpu you want to use.
# allow_nonfree: whether use non-empty gpu when there is no enough of them.
# ask: if is set to true, the script will ask for a confirmation when using non empty gpu. if false, it will use the non empty gpu directly.
# blacklist: a list of int, the gpu in this list will not be used unless you mannuly choose them.
def auto_set(num, allow_nonfree=True, ask=True, blacklist=[], show=True):
	# some code here.
```

