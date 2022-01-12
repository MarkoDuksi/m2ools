#!/usr/bin/env python
# coding: utf-8

import random
from functools import wraps

# set JITTER_SIGMA_COUNT to a reasonable default of 4
# do not change, tune the `jitterfactor` parameter instead
JITTER_SIGMA_COUNT = 4


def get_jitter(val, jitterfactor):
    """Returns a jitter value sampled from a cropped normal distribution.

    Mean of the jitter value is zero. Standard deviation is an absolute
    value of `val` scaled by `jitterfactor` and normalized by a constant
    JITTER_SIGMA_COUNT. For JITTER_SIGMA_COUNT = 4 and jitterfactor = 1
    sampling from this distribution yields a jitter value within a range
    of +/- base value `val` 99.99 % of the time. The results are cropped
    (not clipped) to that range.

    Example
    -------
    # samples from random.gauss(0, 0.25) and crops to <-10, 10> ensuring
    # that 0 < (10 + jitter) < 20
    >>> jitter = get_jitter(val=10, jitterfactor=1)
    """

    if jitterfactor <= 0 or val == 0:
        return 0

    base_value = abs(val)
    mean = 0
    std = base_value * jitterfactor / JITTER_SIGMA_COUNT
    jitter_amount = random.gauss(mean, std)

    # repeat if result is outside of +/- 4 sigma (JITTER_SIGMA_COUNT = 4)
    while abs(jitter_amount) >= (std * JITTER_SIGMA_COUNT):
        jitter_amount = random.gauss(mean, std)

    return jitter_amount


def get_jittered(val, jitterfactor):
    return val + get_jitter(val, jitterfactor)


# jitters result of a function
def m2jitter(_func=None, *, jitterfactor=1):
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


def m2jitterargs(_func=None, *, jitterfactors=(1,)):
    """Jitters int or float arguments of a funtion.

    Jitterfactor for n-th argument of the decorated function is provided
    by the value of n-th member of `jitterfactors` tuple. Any extra
    jitterfactors are ignored. If there is less jitterfactors than there
    are arguments to a function, extra arguments remain unaffected.
    Non- int or float arguments remain unaffected.
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


def test1():
    import numpy as np
    from matplotlib import pyplot as plt

    NUM_POINTS = 1000

    F1_JITTERFACTOR = 0.5
    F2_JITTERFACTOR = 1
    F3_JITTERFACTOR = 2

    # define functions to jitter
    def f1(x):
        return -0.25 * x

    def f2(x):
        return 0.0027 * x ** 3

    def f3(x):
        return -np.sin(x)

    # spread 1000 x-points
    x = np.linspace(-10, 10, NUM_POINTS)

    # get regular f(x)
    y1 = np.array([f1(var) for var in x])
    y2 = np.array([f2(var) for var in x])
    y3 = np.array([f3(var) for var in x])

    # get jittered f(x)
    y1_jittered = [m2jitter(jitterfactor=F1_JITTERFACTOR)(f1)(var) for var in x]
    y2_jittered = [m2jitter(jitterfactor=F2_JITTERFACTOR)(f2)(var) for var in x]
    y3_jittered = [m2jitter(jitterfactor=F3_JITTERFACTOR)(f3)(var) for var in x]

    print(f'\n{len(y1_jittered) = :,}\n{min(y1_jittered) = :.4f}\n{max(y1_jittered) = :.4f}')
    print(f'\n{len(y2_jittered) = :,}\n{min(y2_jittered) = :.4f}\n{max(y2_jittered) = :.4f}')
    print(f'\n{len(y3_jittered) = :,}\n{min(y3_jittered) = :.4f}\n{max(y3_jittered) = :.4f}')

    # visualize
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.axhline(0, color='#777777')
    ax.plot(x, y1_jittered, color='tab:blue', label=f'f(x) = -0.25 * x; jitterfactor = {F1_JITTERFACTOR}')
    ax.plot(x, y2_jittered, color='tab:orange', label=f'f(x) = 0.0027 * x^3; jitterfactor = {F2_JITTERFACTOR}')
    ax.plot(x, y3_jittered, color='tab:green', label=f'f(x) = -sin(x); jitterfactor = {F3_JITTERFACTOR}')
    ax.plot(x, y1, color='#777777')
    ax.plot(x, y2, color='#777777')
    ax.plot(x, y3, color='#777777')
    ax.fill_between(x, y1 * (1 - F1_JITTERFACTOR), y1 * (1 + F1_JITTERFACTOR), color='tab:blue', alpha=0.5)
    ax.fill_between(x, y2 * (1 - F2_JITTERFACTOR), y2 * (1 + F2_JITTERFACTOR), color='tab:orange', alpha=0.5)
    ax.fill_between(x, y3 * (1 - F3_JITTERFACTOR), y3 * (1 + F3_JITTERFACTOR), color='tab:green', alpha=0.5)
    ax.legend()
    plt.title('Effect of jitterfactor on jitter spread')
    plt.show()


def test2():
    @m2jitterargs(jitterfactors=(1, 1, 1, 1, 1, 1, 1, 1))
    def printargs(a, b, c, d, e, f=10):
        print(f'{a = :.3f}\n{b = :.3f}\n{c = :.3f}\n{d = :.3f}\n{e = :.3f}\n{f = :.3f}')

    printargs(10, 10, 10, d=10, e=10, f=10)


if __name__ == '__main__':
    test1()
    print()
    test2()
