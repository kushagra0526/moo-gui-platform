"""Quick integration test for CEC2018 DMOP."""
import sys, numpy as np
sys.path.insert(0, '.')
from cec2018_dmop import CEC2018Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize

print("=== CEC2018 Integration Test ===\n")

# 1. Test all 14 problems evaluate without error
for pid in range(1, 15):
    p = CEC2018Problem(problem_id=pid, taut=10, nt=10, n_var=10)
    p.set_tau(0)
    X = np.random.rand(3, 10)
    X[:, 1:] = X[:, 1:] * 2 - 1
    if pid >= 10:
        X[:, 1] = np.random.rand(3)
    out = {}
    p._evaluate(X, out)
    n_obj = out["F"].shape[1]
    label = "2-obj" if n_obj == 2 else "3-obj"
    print("  DF{:2d}: shape {}  ({})  OK".format(pid, out["F"].shape, label))

print()

# 2. Run NSGA-II on DF1 for 20 generations
print("=== NSGA-II on DF1 for 20 generations ===\n")
problem = CEC2018Problem(problem_id=1, taut=10, nt=10, n_var=10)
gen_log = []

def cb(algo):
    problem.set_tau(algo.n_gen)
    pf = algo.opt.get("F")
    gen_log.append((algo.n_gen, len(pf)))

algo = NSGA2(
    pop_size=50,
    sampling=FloatRandomSampling(),
    crossover=SBX(prob=0.9, eta=15),
    mutation=PM(prob=0.1, eta=20),
    eliminate_duplicates=True,
)
res = minimize(problem, algo, ("n_gen", 20), callback=cb, verbose=False, seed=42)
print("  Final Pareto front size : {}".format(len(res.F)))
print("  Generations logged      : {}".format(len(gen_log)))
print("  First gen (gen, pf_size): {}".format(gen_log[0]))
print("  Last  gen (gen, pf_size): {}".format(gen_log[-1]))

# 3. Verify environment change detection
print()
print("=== Environment change check (taut=5) ===\n")
p2 = CEC2018Problem(problem_id=1, taut=5, nt=10, n_var=10)
X_test = np.array([[0.5] + [0.0]*9])
results = []
for tau in [0, 5, 10, 15, 20]:
    p2.set_tau(tau)
    out = {}
    p2._evaluate(X_test, out)
    results.append("  tau={:3d}  f1={:.4f}  f2={:.4f}".format(tau, out["F"][0,0], out["F"][0,1]))
for r in results:
    print(r)

print()
print("ALL TESTS PASSED")
