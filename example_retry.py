#!/usr/bin/env python
# coding: utf-8

import m2ools as m2
import random
from matplotlib import pyplot as plt


def example():
    NUM_POINTS = 5000

    # validate myfunc result, retry if invalid (max 5 tries, no delay between tries)
    @m2.retry(validator=lambda x: x > 9 or x < 7, maxtries=5, delay=0, jitterfactor=1, backoff=False, boexpbase=2, borandom=False)
    def myfunc(meanval, stddev):
        return random.gauss(meanval, stddev)

    # catch an exception raised if invalid result is returned on 5 subsequent calls
    # to ensure that returned list is populated with all `size` points
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


if __name__ == '__main__':
    example()
