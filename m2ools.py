#!/usr/bin/env python
# coding: utf-8

import os
import re
import random
import pickle
import hashlib
import pandas as pd
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta
from time import sleep


########################################################################
# jitter functionalities
########################################################################

# set JITTER_SIGMA_COUNT to a reasonable default of 4
# not meant to be changed, tune the `jitterfactor` instead
JITTER_SIGMA_COUNT = 4


def get_jitter(val, jitterfactor):
    """Return a jitter value sampled from a cropped normal distribution.

    Mean of the jitter value is zero. Standard deviation is an absolute
    value of `val` scaled by `jitterfactor` and normalized by a constant
    `JITTER_SIGMA_COUNT`. For JITTER_SIGMA_COUNT = 4 and jitterfactor = 1
    sampling from this distribution yields a jitter value within a range
    of +/- base value `val` 99.99 % of the time. Crop the result to that
    range.

    Example
    -------
    # sample from random.gauss(0, 2.5) and crop to <-10, 10> ensuring
    # that 0 < (10 + jitter) < 20
    >>> jitter = get_jitter(val=10, jitterfactor=1)
    """

    if isinstance(val, (int, float)):
        if val == 0:
            return 0
    else:
        raise TypeError('Argument to `jitterfactor` must be of type int or float.')

    if isinstance(jitterfactor, (int, float)):
        if jitterfactor < 0:
            raise ValueError('Argument to `jitterfactor` must not be negative.')
        elif jitterfactor == 0:
            return 0
    else:
        raise TypeError('Argument to `jitterfactor` must be of type int or float.')

    base_value = abs(val)
    mean = 0
    std = base_value * jitterfactor / JITTER_SIGMA_COUNT
    # jitter_amount = random.gauss(mean, std)

    # repeat sampling if outside of +/- 4 sigma (JITTER_SIGMA_COUNT = 4)
    while abs(jitter_amount := random.gauss(mean, std)) >= (std * JITTER_SIGMA_COUNT):
        pass

    return jitter_amount


# helper function
def get_jittered(val, jitterfactor):
    return val + get_jitter(val, jitterfactor)


def jitter(_func=None, *, jitterfactor=1):
    """Jitter the return value of a function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return get_jittered(result, jitterfactor)
        return wrapper
    if _func is None:
        return decorator
    else:
        return decorator(_func)


def jitterargs(_func=None, *, jitterfactors=(1,)):
    """Jitter int or float arguments of a funtion.

    Jitterfactor for n-th argument of the decorated function is provided
    by the value of n-th member of `jitterfactors` tuple. Any extra
    jitterfactors are ignored. If there is less jitterfactors than there
    are arguments to a function, extra arguments remain unaffected.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            jitterfactors = wrapper.jitterfactors
            newargs = list(args)
            for idx, jfactor in enumerate(jitterfactors[:len(args)]):
                if jfactor >= 0 and isinstance(args[idx], (int, float)):
                    newargs[idx] = get_jittered(args[idx], jfactor)
            for jfactor, key in zip(jitterfactors[len(args):], kwargs):
                if jfactor >= 0 and isinstance(kwargs[key], (int, float)):
                    kwargs[key] = get_jittered(kwargs[key], jfactor)
            return func(*newargs, **kwargs)
        wrapper.jitterfactors = jitterfactors
        return wrapper
    if _func is None:
        return decorator
    else:
        return decorator(_func)


########################################################################
# retry functionality
########################################################################

class MaxTriesExhaustedError(Exception):
    pass


def retry(_func=None, *, validator=lambda x: True, maxtries=1, delay=0, jitterfactor=0, backoff=False, boexpbase=1, borandom=False):
    """Retry a callable until its return value passes validation.

    Parameters
    ----------
    validator : callable, default=lambda x: True
        Validates return value(s). Should return True if valid, False otherwise.
        Defaults to always returning True.
    maxtries : int, default=1
        Maximum number of calls before raising an exception.
    delay : int or float, default=0
        Time to sleep after an invalid result.
    jitterfactor : int or float, default=0
        Time to sleep is jittered if set to greater than zero. Maximum is 1.
    backoff : bool, default=False
        Time to sleep is exponentially prolonged at each step.
    boexpbase : int or float, default=1
        Sets the base of exponential backoff.
    barandom : bool, default=False
        Sets backoff strategy to randomly choose the exponent at each step up to
        the step-wise maximum one. For maximum randomness set this to True and
        `jitterfactor` to 1.
    """

    if not callable(validator):
        raise TypeError('First argument must be of callable type.')

    if isinstance(maxtries, int):
        if maxtries < 1:
            raise ValueError('Argument to `maxtries` must be equal or greater than 1.')
    else:
        raise TypeError('Argument to `maxtries` must be of type integer.')

    if isinstance(delay, (int, float)):
        if delay < 0:
            raise ValueError('Argument to `delay` must be equal or greater than 0.')
    else:
        raise TypeError('Argument to `delay` must be of type integer or float.')

    if isinstance(jitterfactor, (int, float)):
        if jitterfactor < 0 or jitterfactor > 1:
            raise ValueError('Argument to `jitterfactor` can range only from 0 to 1 (both inclusive).')
    else:
        raise TypeError('Argument to `jitterfactor` must be of type integer or float.')

    if not isinstance(backoff, bool):
        raise TypeError('Argument to `backoff` must be of type bool.')

    if isinstance(boexpbase, (int, float)):
        if boexpbase < 1:
            raise ValueError('Argument to `boexpbase` must be equal or greater than 1.')
    else:
        raise TypeError('Argument to `boexpbase` must be of type integer or float.')

    if not isinstance(borandom, bool):
        raise TypeError('Argument to `borandom` must be of type bool.')

    if not delay:
        jitterfactor = 0
        backoff = False

    if not backoff:
        boexpbase = 1

    if boexpbase == 1:
        borandom = False

    if borandom:
        def exponent(failcount):
            return random.choice([exponent for exponent in range(failcount)])
    else:
        def exponent(failcount):
            return failcount - 1

    @jitter(jitterfactor=jitterfactor)
    def get_waiting_time(boexpbase, failcount, delay):
        return boexpbase ** (exponent(failcount)) * delay

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            remaining_tries = maxtries
            failcount = 0
            while remaining_tries:
                if validator((result := func(*args, **kwargs))):
                    failcount = 0
                    return result
                failcount += 1
                remaining_tries -= 1
                if delay and remaining_tries:
                    time_to_wait = get_waiting_time(boexpbase, failcount, delay)
                    sleep(time_to_wait)
            else:
                raise MaxTriesExhaustedError(f'{func.__name__}({", ".join([str(arg) for arg in args]) + ", ".join([f"{k}={v!r}" for k, v in kwargs.items()])}) failed {failcount} times, returning None.')
        return wrapper
    if _func is None:
        return decorator
    else:
        return decorator(_func)


########################################################################
# cache functionality
########################################################################

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


def cache(_func=None, *, reachback=datetime.min.strftime('%Y-%m-%d'), hoard=False, cachedir=CACHE_DIR):
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
