"""
CEC2018 Dynamic Multi-Objective Optimization Problems.
Python 3 port of the MATLAB implementation by A. Cheriet.
Source: https://github.com/ahcheriet/CEC2018_DMOP

Function signature:
    cec2018_DF(problemID, x, tau, taut, nt) -> dict {0: f1, 1: f2, [2: f3]}

Parameters
----------
problemID : int   1–14
x         : array-like  decision vector (n_var=10)
tau       : int   current generation counter
taut      : int   change frequency (generations per environment)
nt        : float change severity
"""

import numpy as np


def cec2018_DF(problemID, x, tau, taut, nt):
    x = np.asarray(x, dtype=float)
    n = len(x)
    T0 = 50

    # Time parameter
    t = (1.0 / nt) * np.floor(max(tau + taut - T0 - 1, 0) / taut)

    f = {}

    if problemID == 1:
        G = np.sin(0.5 * np.pi * t)
        H = 0.75 * np.sin(0.5 * np.pi * t) + 1.25
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(1, n)])
        f[0] = x[0]
        f[1] = g * (1.0 - (x[0] / g) ** H)

    elif problemID == 2:
        G = np.abs(np.sin(0.5 * np.pi * t))
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(1, n)])
        f[0] = x[0]
        f[1] = g * (1.0 - np.sqrt(x[0] / g))

    elif problemID == 3:
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(1, n)])
        f[0] = x[0]
        f[1] = g * (1.0 - (x[0] / g) ** 2)

    elif problemID == 4:
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(1, n)])
        f[0] = x[0]
        f[1] = g * (1.0 - np.sqrt(x[0] / g) - (x[0] / g) * np.sin(2.0 * np.pi * x[0]))

    elif problemID == 5:
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(1, n)])
        f[0] = x[0] + 0.1 * np.sin(3.0 * np.pi * x[0])
        f[1] = g * (1.0 - x[0] / g) + 0.1 * np.sin(3.0 * np.pi * x[0])

    elif problemID == 6:
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(1, n)])
        f[0] = x[0]
        f[1] = g * (1.0 - x[0] / g)

    elif problemID == 7:
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(1, n)])
        f[0] = x[0]
        f[1] = g * (1.0 - (x[0] / g) ** 2)

    elif problemID == 8:
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(1, n)])
        f[0] = x[0]
        f[1] = g * (1.0 - np.sqrt(x[0] / g))

    elif problemID == 9:
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(1, n)])
        f[0] = x[0]
        f[1] = g * (1.0 - (x[0] / g) ** 2)

    elif problemID == 10:
        # 3-objective
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(2, n)])
        f[0] = x[0] * x[1]
        f[1] = x[0] * (1.0 - x[1])
        f[2] = g * (1.0 - x[0])

    elif problemID == 11:
        # 3-objective
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(2, n)])
        f[0] = np.cos(0.5 * np.pi * x[0]) * np.cos(0.5 * np.pi * x[1])
        f[1] = np.cos(0.5 * np.pi * x[0]) * np.sin(0.5 * np.pi * x[1])
        f[2] = g * np.sin(0.5 * np.pi * x[0])

    elif problemID == 12:
        # 3-objective
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(2, n)])
        f[0] = x[0]
        f[1] = x[1] * (1.0 - x[0])
        f[2] = g * (1.0 - x[0])

    elif problemID == 13:
        # 3-objective
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(2, n)])
        f[0] = x[0]
        f[1] = g * x[1] * (1.0 - x[0] / g)
        f[2] = g * (1.0 - x[0] / g)

    elif problemID == 14:
        # 3-objective
        G = np.sin(0.5 * np.pi * t)
        g = 1.0 + np.sum([(x[i] - G) ** 2 for i in range(2, n)])
        f[0] = x[0]
        f[1] = x[1]
        f[2] = g * (1.0 - x[0] - x[1])

    else:
        raise ValueError(f"problemID must be 1–14, got {problemID}")

    return f
