#!/usr/bin/env python
# coding: utf-8

import os
import re
import pickle
import hashlib
import pandas as pd
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta

CACHE_DIR = 'cache'


def get_cache_inventory(cachedir, func_name):
    cache_inventory = defaultdict(list)
    cachefilename_re = re.compile(func_name + r'_([0-9a-f]{40})_(\d{4}-\d{2}-\d{2}_\d{6})\.(?:csv|pkl)$')

    for root, _, filenames in os.walk(cachedir):
        for filename in filenames:
            if (match := cachefilename_re.match(filename)):
                func_sig_hashed = match.group(1)
                timestamp = match.group(2)
                dt = datetime.strptime(timestamp, '%Y-%m-%d_%H%M%S')
                cachefilename = os.path.join(root, filename)
                cache_inventory[func_sig_hashed].append({'dt': dt,
                                                         'cachefilename': cachefilename})
    return cache_inventory


def get_func_sig_hashed(name, args, kwargs):
    argslist = [repr(arg) for arg in args]
    kwargslist = [f'{k}={v!r}' for k, v in kwargs.items()]
    allargs = ', '.join(argslist + kwargslist)
    func_sig = f'{name}({allargs})'
    func_sig_hashed = hashlib.sha1(func_sig.encode('utf-8')).hexdigest()
    return func_sig_hashed


def to_cache(result, cachedir, func_name, func_sig_hashed):
    os.makedirs(cachedir, exist_ok=True)
    dt = datetime.now()
    cachebasefilename = os.path.join(cachedir, func_name + '_' + func_sig_hashed + dt.strftime('_%Y-%m-%d_%H%M%S'))
    if isinstance(result, pd.DataFrame):
        cachefilename = cachebasefilename + '.csv'
        print(f'caching result for {func_name}: {cachefilename}')
        result.to_csv(cachefilename)
    else:
        cachefilename = cachebasefilename + '.pkl'
        print(f'caching result for {func_name}: {cachefilename}')
        with open(cachefilename, 'wb') as cachefile:
            pickle.dump(result, cachefile)
    return dt, cachefilename


def from_cache(cachefilename, func_name):
    print(f'fetching cached result for {func_name}: {cachefilename}')
    ext = cachefilename[-4:]
    if ext == '.csv':
        result = pd.read_csv(cachefilename, index_col=0)
    elif ext == '.pkl':
        with open(cachefilename, 'rb') as cachefile:
            result = pickle.load(cachefile)
    return result


def get_dt(reachback):
    datetime_re = r'(\d{1,4})(?:\D(\d{1,2}))?(?:\D(\d{1,2}))?(?:\D(\d{1,2}))?(?:\D(\d{1,2}))?(?:\D(\d{1,2}))?$'
    customtimedelta_re = r'(\d+) *(year|month|week|day|hour|minute|second)s?'
    if (match := re.match(datetime_re, reachback)):
        dt_args = [int(x) if x else 1 for x in match.groups()[:3]]
        dt_args += [int(x) if x else 0 for x in match.groups()[3:]]
    elif (matches := re.findall(customtimedelta_re, reachback)):
        tdelta_args = {f'{k}s': int(v) for v, k in matches if k in ['week', 'day', 'hour', 'minute', 'second']}
        custom_args = {f'{k}s': int(v) for v, k in matches if k in ['year', 'month']}
        dt = datetime.now() - timedelta(**tdelta_args)
        month = dt.month - custom_args.get('months', 0)
        year = dt.year - custom_args.get('years', 0)
        while month <= 0:
            month += 12
            year -= 1
        dt_args = [year, month, dt.day, dt.hour, dt.minute, dt.second]
    return datetime(*dt_args)


def m2cache(_func=None, *, reachback=datetime.min.strftime('%Y-%m-%d'), hoard=False, cachedir=CACHE_DIR):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_sig_hashed = get_func_sig_hashed(func.__name__, args, kwargs)
            if func_sig_hashed in wrapper.cache_inventory \
                and (most_recent_cached_entry := max(wrapper.cache_inventory[func_sig_hashed],
                                                     key=lambda d: d['dt']))['dt'] >= get_dt(reachback):
                cachefilename = most_recent_cached_entry['cachefilename']
                result = from_cache(cachefilename, func.__name__)
            else:
                if (result := func(*args, **kwargs)) is not None:
                    dt, cachefilename = to_cache(result, cachedir, func.__name__, func_sig_hashed)
                    if not hoard:
                        stale_files = [entry.get('cachefilename', '') for entry in wrapper.cache_inventory.get(func_sig_hashed, [])]
                        for file in stale_files:
                            os.remove(file)
                        wrapper.cache_inventory[func_sig_hashed] = []
                    wrapper.cache_inventory.get(func_sig_hashed, []).append({'dt': dt,
                                                                             'cachefilename': cachefilename})
                else:
                    print('result was None')
            return result
        wrapper.cache_inventory = get_cache_inventory(cachedir, func.__name__)
        return wrapper
    if _func is None:
        return decorator
    else:
        return decorator(_func)


def main():
    import random
    from matplotlib import pyplot as plt
    from m2retry import m2retry, MaxTriesExhaustedError

    NUM_POINTS = 5000

    @m2retry(validator=lambda x: x > 9 or x < 7, maxtries=5, delay=0.003, jitterfactor=0, backoff=False, boexpbase=2, borandom=False)
    def myfunc(meanval, stddev):
        return random.gauss(meanval, stddev)

    @m2cache(cachedir=CACHE_DIR, reachback='1 minute', hoard=False)
    def get_y(meanval, stddev, size):
        y = []
        while size:
            try:
                result = myfunc(meanval, stddev)
            except MaxTriesExhaustedError as e:
                print(f'Exception: {e}')
            else:
                y.append(result)
                size -= 1
        return y

    y1 = get_y(10, 3, NUM_POINTS)
    print(f'\n{len(y1) = :,}\n{min(y1) = :.4f}\n{max(y1) = :.4f}\n')

    # histogram
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.hist(y1, bins=40)
    ax.set_xlim(0, 20)
    ax.xaxis.set(ticks=range(0, 20, 2))
    plt.title(f'gauss(10, 2.9): {NUM_POINTS} points excluding interval [7, 9]')
    plt.show()

    # 2D scatter
    y2 = get_y(11, 4, NUM_POINTS)
    print(f'\n{len(y2) = :,}\n{min(y2) = :.4f}\n{max(y2) = :.4f}\n')

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(y1, y2)
    ax.set_xlim(0, 20)
    ax.xaxis.set(ticks=range(-2, 24, 2))
    ax.yaxis.set(ticks=range(-2, 24, 2))
    plt.title(f'gauss(11, 4) vs. gauss(10, 2.9): {NUM_POINTS} points excluding interval [7, 9]')
    plt.show()


def main2():
    print(get_dt(datetime.min.strftime('%Y-%m-%d')))
    print(get_dt('2000-12'))
    print(get_dt('20 years'))
    print(get_dt('20 years, 25 months, 79 days, 36 hours, 300 minutes'))
    # print(get_dt('2020 years, 9 months, 9 days, 12 hours, 59 minutes'))


if __name__ == '__main__':
    main()
