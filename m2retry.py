#!/usr/bin/env python
# coding: utf-8

import random
from time import sleep
from functools import wraps
from m2jitter import m2jitter


class MaxTriesExhaustedError(Exception):
    pass


def m2retry(_func=None, *, validator=lambda x: True, maxtries=1, delay=0, jitterfactor=0, backoff=False, boexpbase=1, borandom=False):
    """Retries a callable until result is validated.

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
        Time to sleep is expontially prolonged at each step.
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

    @m2jitter(jitterfactor=jitterfactor)
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


def main():
    from matplotlib import pyplot as plt

    NUM_POINTS = 5000

    # validate myfunc result, retry if invalid (max 5 tries, no delay between tries)
    @m2retry(validator=lambda x: x > 9 or x < 7, maxtries=5, delay=0, jitterfactor=0, backoff=False, boexpbase=2, borandom=False)
    def myfunc(meanval, stddev):
        return random.gauss(meanval, stddev)

    # myfunc now raises an exception if invalid result is returned on 5 subsequent calls
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

    y1 = get_y(10, 2.9, NUM_POINTS)
    print(f'\n{len(y1) = :,}\n{min(y1) = :.4f}\n{max(y1) = :.4f}')

    # histogram
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.hist(y1, bins=40)
    ax.set_xlim(0, 20)
    ax.xaxis.set(ticks=range(0, 20, 2))
    plt.title(f'gauss(10, 2.9): {NUM_POINTS} points excluding interval [7, 9]')
    plt.show()

    # 2D scatter
    y2 = get_y(11, 4, NUM_POINTS)
    print(f'\n{len(y2) = :,}\n{min(y2) = :.4f}\n{max(y2) = :.4f}')

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(y1, y2)
    ax.set_xlim(0, 20)
    ax.xaxis.set(ticks=range(-2, 24, 2))
    ax.yaxis.set(ticks=range(-2, 24, 2))
    plt.title(f'gauss(11, 4) vs. gauss(10, 2.9): {NUM_POINTS} points excluding interval [7, 9]')
    plt.show()


if __name__ == '__main__':
    main()
