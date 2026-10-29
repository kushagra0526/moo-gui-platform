"""
ISVM-DMOEA (Xu et al., IEEE TEVC 26(4), 2022, Algorithm 3) on the CEC2018 DF problems, with NSGA-II as
the static optimizer, plus the MIGD/MHV metrics (Eqs. 17-20).

Usage:
    from dmoea import run
    result = run(2, nt=10, taut=10, strategy="isvm", oversampling="loras", seed=1)
    result["migd"], result["mhv"]
"""

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.indicators.hv import HV
from pymoo.indicators.igd import IGD
from pymoo.optimize import minimize

from cec2018_dmop import CEC2018Problem, N_OBJ, true_front
from .oversampling import training_set
from .predictor import ISVMPredictor

# shortcut: pymoo samples DF9 by filtering 1000 points and DF10-DF14 on a fixed 20x20 grid, so those
# true fronts have 144-502 points instead of the paper's 1000; densify if their IGD disagrees with the paper.
TRUE_FRONT_POINTS = 1000


def igd(F, pf):
    """Mean distance from each true-front point to its nearest found point (Eq. 17)."""
    return float(IGD(pf).do(F))


def hv(F, pf):
    """Hypervolume of F with the reference point at each objective's maximum on the true front (Eq. 19)."""
    return float(HV(ref_point=pf.max(axis=0)).do(F))


def run(problem_id, nt=10, taut=10, n_changes=30, strategy="isvm", oversampling="loras", r=5, k=5,
        pop_size=None, n_var=10, history=True, C=None, gamma=None, seed=0):
    """One run on DF<problem_id>.

    Environment e lasts taut generations at time t = e / nt (the paper's t = floor(tau / taut) / nt);
    there are n_changes changes after the first environment, at known times. On each change the next
    initial population is predicted by the ISVM (strategy "isvm") or drawn at random (strategy "random",
    the paper's DA baseline). Population size defaults to 100 for 2 objectives and 150 for 3.

    Returns per-environment "igd" and "hv" (measured at the end of each environment), "migd" and "mhv"
    averaged over the n_changes environments that follow a change (Eqs. 18 and 20), "migd_every_gen"
    (IGD averaged over every generation of those environments, the other common MIGD convention), the
    ISVM "acceptance" rate per change, and the tuned "C" and "gamma".
    """
    rng = np.random.default_rng(seed)
    problem = CEC2018Problem(problem_id, taut=taut, nt=nt, n_var=n_var)
    xl, xu = problem.xl, problem.xu
    pop_size = pop_size or (100 if N_OBJ[problem_id] == 2 else 150)
    predictor = ISVMPredictor(history, C, gamma)

    X0 = xl + rng.random((pop_size, n_var)) * (xu - xl)
    igds, hvs, every_gen, acceptance = [], [], [], []
    for env in range(n_changes + 1):
        problem.time = env / nt
        pf = true_front(problem_id, problem.time, TRUE_FRONT_POINTS)

        def track(algorithm):  # every-generation IGD, counted only after a change
            if env:
                every_gen.append(igd(algorithm.opt.get("F"), pf))

        res = minimize(problem, NSGA2(pop_size=pop_size, sampling=X0), ("n_gen", taut),
                       seed=int(rng.integers(2 ** 31)), callback=track, verbose=False)
        igds.append(igd(res.F, pf))
        hvs.append(hv(res.F, pf))
        if env == n_changes:
            break

        # Environment changes: build the next initial population
        if strategy == "random":
            X0 = xl + rng.random((pop_size, n_var)) * (xu - xl)
        else:
            X, y = training_set(res.X, xl, xu, oversampling, r, k, rng)
            predictor.update(X, y)
            U, found, draws = predictor.predict_population(pop_size, rng)
            X0 = xl + U * (xu - xl)
            acceptance.append(found / draws)

    return {
        "igd": igds,
        "hv": hvs,
        "migd": float(np.mean(igds[1:])),
        "mhv": float(np.mean(hvs[1:])),
        "migd_every_gen": float(np.mean(every_gen)),
        "acceptance": acceptance,
        "C": predictor.C,
        "gamma": predictor.gamma,
    }
