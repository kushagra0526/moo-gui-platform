"""
Oversampling of the last Pareto-optimal set (POS) into a balanced SVM training set.

Follows POSMOTE (Xu et al., IEEE TEVC 26(4), 2022, Algorithm 1). The SMOTE step can be swapped for
LoRAS (Bej et al., Machine Learning 110, 2021); everything else stays the same.

All functions work in the unit cube: decision variables are scaled by their bounds first, so neighbour
distances and LoRAS noise do not depend on each variable's range.
"""

import numpy as np


def _neighbours(P, k):
    """Indices of the k nearest other rows of P (Euclidean); fewer when P has fewer than k + 1 rows."""
    k = min(k, len(P) - 1)
    d = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    return np.argsort(d, axis=1)[:, :k]


def smote(P, r, k, rng):
    """r synthetic points per row of P, each on the segment to one of its k nearest neighbours (Eq. 16)."""
    n, D = P.shape
    base = np.repeat(np.arange(n), r)
    nbr = _neighbours(P, k)
    if nbr.shape[1] == 0:  # a single solution has no neighbour to interpolate towards
        return P[base].copy()
    partner = nbr[base, rng.integers(nbr.shape[1], size=len(base))]
    gap = rng.random((len(base), 1))  # one scalar per point keeps it on the segment, as in the paper's Fig. 3
    return P[base] + gap * (P[partner] - P[base])


def loras(P, r, k, rng, sigma=0.005, n_shadow=40, n_aff=None):
    """r LoRAS points per row of P.

    Each row and its k nearest neighbours form a neighbourhood; every member gets n_shadow Gaussian
    "shadow" copies (std sigma), and each new point is a Dirichlet-weighted convex combination of n_aff
    shadows drawn from that neighbourhood. n_aff defaults to the number of variables.
    """
    n, D = P.shape
    n_aff = n_aff or D
    nbr = _neighbours(P, k)
    out = np.empty((n * r, D))
    for i in range(n):
        hood = P[np.r_[i, nbr[i]]]
        shadows = np.repeat(hood, n_shadow, axis=0) + rng.normal(0.0, sigma, (len(hood) * n_shadow, D))
        m = min(n_aff, len(shadows))
        pick = np.argsort(rng.random((r, len(shadows))), axis=1)[:, :m]  # m distinct shadows per new point
        weights = rng.dirichlet(np.ones(m), size=r)
        out[i * r:(i + 1) * r] = np.einsum("ra,rad->rd", weights, shadows[pick])
    return out


OVERSAMPLERS = {"smote": smote, "loras": loras}


def training_set(pos, xl, xu, method, r, k, rng):
    """Balanced training set in the unit cube (Algorithm 1).

    Positives: the POS plus r synthetic points per solution. Negatives: as many uniform random points.
    Returns (X, y) with y = +1 for positives and -1 for negatives.
    """
    U = (pos - xl) / (xu - xl)
    synthetic = OVERSAMPLERS[method](U, r, k, rng) if r else np.empty((0, U.shape[1]))
    positives = np.clip(np.vstack([U, synthetic]), 0.0, 1.0)
    negatives = rng.random(positives.shape)
    X = np.vstack([positives, negatives])
    y = np.r_[np.ones(len(positives)), -np.ones(len(negatives))]
    return X, y
