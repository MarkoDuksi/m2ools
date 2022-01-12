#!/usr/bin/env python
# coding: utf-8

import m2ools as m2
import numpy as np
from matplotlib import pyplot as plt


def example1():
    NUM_POINTS = 1000

    # jitterfactors to compare
    F1_JITTERFACTOR = 0.5
    F2_JITTERFACTOR = 1
    F3_JITTERFACTOR = 2

    # define sample functions to jitter and compare
    def f1(x):
        return -0.25 * x

    def f2(x):
        return 0.0027 * x ** 3

    def f3(x):
        return -np.sin(x)

    # spread NUM_POINTS x-points
    x = np.linspace(-10, 10, NUM_POINTS)

    # get regular f(x)
    y1 = np.array([f1(var) for var in x])
    y2 = np.array([f2(var) for var in x])
    y3 = np.array([f3(var) for var in x])

    # get jittered f(x)
    y1_jittered = [m2.jitter(jitterfactor=F1_JITTERFACTOR)(f1)(var) for var in x]
    y2_jittered = [m2.jitter(jitterfactor=F2_JITTERFACTOR)(f2)(var) for var in x]
    y3_jittered = [m2.jitter(jitterfactor=F3_JITTERFACTOR)(f3)(var) for var in x]

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


def example2():
    @m2.jitterargs(jitterfactors=(1, 1, 1, 1, 1))
    def printargs(a, b, c, d, e, f=10):
        print(f'\n{a = }\n{b = :.2f}\n{c = :.2f}\n{d = :.2f}\n{e = :.2f}\n{f = :.2f}')

    printargs('teststring', 10, 10, d=10, e=10, f=10)


if __name__ == '__main__':
    example1()
    example2()
