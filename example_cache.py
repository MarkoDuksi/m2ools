#!/usr/bin/env python
# coding: utf-8

import m2ools as m2
import random
from matplotlib import pyplot as plt
from datetime import datetime


def example1():
    NUM_POINTS = 5000

    @m2.retry(validator=lambda x: x > 9 or x < 7, maxtries=5, delay=0.01, jitterfactor=1, backoff=False, boexpbase=2, borandom=False)
    def myfunc(meanval, stddev):
        return random.gauss(meanval, stddev)

    @m2.cache(cachedir='example_cache', reachback='12 minutes', hoard=False)
    def get_y(meanval, stddev, size):
        y = []
        while size:
            try:
                result = myfunc(meanval, stddev)
            except m2.MaxTriesExhaustedError as e:
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
    plt.title(f'gauss(10, 3): {NUM_POINTS} points excluding interval [7, 9]')
    plt.show()

    # 2D scatter
    y2 = get_y(11, 4, NUM_POINTS)
    print(f'\n{len(y2) = :,}\n{min(y2) = :.4f}\n{max(y2) = :.4f}\n')

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(y1, y2)
    ax.set_xlim(0, 20)
    ax.xaxis.set(ticks=range(-2, 24, 2))
    ax.yaxis.set(ticks=range(-2, 24, 2))
    plt.title(f'gauss(11, 4) vs. gauss(10, 3): {NUM_POINTS} points excluding interval [7, 9]')
    plt.show()


def example2():
    print(m2.get_dt(datetime.min.strftime('%Y-%m-%d')))
    print(m2.get_dt('2000-12'))
    print(m2.get_dt('20 years'))
    print(m2.get_dt('20 years, 25 months, 79 days, 36 hours, 300 minutes'), '\n')
    # print(get_dt('2020 years, 9 months, 9 days, 12 hours, 59 minutes'))


if __name__ == '__main__':
    example1()
    example2()
