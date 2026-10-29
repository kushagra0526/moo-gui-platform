#!/usr/bin/env python3
"""
Benchmark ISVM-DMOEA on CEC2018 DF1-DF14 with the protocol of Xu et al. (IEEE TEVC 26(4), 2022, Sec. V):
10 variables, population 100/150, (nt, taut) in {(10,10), (5,10), (10,5)}, 30 changes, NSGA-II.

    python benchmarks/isvm_benchmark.py run --runs 5 --workers 4    # resumable: finished runs are skipped
    python benchmarks/isvm_benchmark.py tables                       # tables + IGD figure from the CSV

Results are written to experiments/ (git-ignored).
"""

import argparse
import csv
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from scipy.stats import ranksums

from dmoea import run

CONFIGS = [(10, 10), (5, 10), (10, 5)]
ALGORITHMS = {
    "random": dict(strategy="random"),
    "isvm-smote": dict(strategy="isvm", oversampling="smote"),
    "isvm-loras": dict(strategy="isvm", oversampling="loras"),
    # Ablations (paper Table III), selected with --algorithms
    "isvm-r0": dict(strategy="isvm", r=0),
    "loras-r3": dict(strategy="isvm", oversampling="loras", r=3),
    "loras-svm": dict(strategy="isvm", oversampling="loras", history=False),
}
MAIN = ["random", "isvm-smote", "isvm-loras"]
ABLATION = ["random", "isvm-r0", "loras-r3", "loras-svm", "isvm-loras"]
PROPOSED = "isvm-loras"
# Paper Table IV: MIGD averaged over the three configurations with NSGA-II -> (DA-NSGA-II, ISVM-NSGA-II)
PAPER_TABLE_IV = {
    1: (0.5660, 0.4381), 2: (0.4855, 0.3132), 3: (0.6347, 0.3744), 4: (1.9088, 1.2459),
    5: (2.0731, 1.5564), 6: (12.650, 12.299), 7: (12.281, 10.224), 8: (0.6447, 0.7094),
    9: (2.4538, 2.2416), 10: (0.2745, 0.1692), 11: (0.4788, 0.2822), 12: (0.6737, 0.8052),
    13: (2.1968, 1.8398), 14: (1.4877, 1.3651),
}
FIELDS = ["problem", "nt", "taut", "algorithm", "seed", "migd", "migd_every_gen", "mhv",
          "acceptance", "C", "gamma", "seconds", "igd"]
OUT = ROOT / "experiments"


def job(key):
    problem, nt, taut, algorithm, seed, changes = key
    start = time.time()
    r = run(problem, nt=nt, taut=taut, n_changes=changes, seed=seed, **ALGORITHMS[algorithm])
    return {
        "problem": problem, "nt": nt, "taut": taut, "algorithm": algorithm, "seed": seed,
        "migd": r["migd"], "migd_every_gen": r["migd_every_gen"], "mhv": r["mhv"],
        "acceptance": np.mean(r["acceptance"]) if r["acceptance"] else "",
        "C": r["C"] or "", "gamma": r["gamma"] or "", "seconds": round(time.time() - start, 1),
        "igd": json.dumps([round(v, 6) for v in r["igd"]]),
    }


def read_rows(path):
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def run_benchmark(path, runs, workers, problems, algorithms, changes):
    done = {(int(r["problem"]), int(r["nt"]), int(r["taut"]), r["algorithm"], int(r["seed"]))
            for r in read_rows(path)}
    jobs = [(p, nt, tt, a, s, changes) for s in range(1, runs + 1) for p in problems
            for nt, tt in CONFIGS for a in algorithms if (p, nt, tt, a, s) not in done]
    print(f"{len(jobs)} runs to do, {len(done)} already in {path}", flush=True)
    new_file = not path.exists()
    with open(path, "a", newline="") as f, Pool(workers) as pool:
        writer = csv.DictWriter(f, FIELDS)
        if new_file:
            writer.writeheader()
        for i, row in enumerate(pool.imap_unordered(job, jobs), 1):
            writer.writerow(row)
            f.flush()  # each finished run is kept even if the benchmark is interrupted
            print(f"[{i}/{len(jobs)}] DF{row['problem']} ({row['nt']},{row['taut']}) {row['algorithm']} "
                  f"seed {row['seed']}: MIGD {row['migd_every_gen']:.4f} in {row['seconds']}s", flush=True)


def collect(rows, metric):
    """{(problem, nt, taut, algorithm): values over seeds}"""
    out = {}
    for r in rows:
        out.setdefault((int(r["problem"]), int(r["nt"]), int(r["taut"]), r["algorithm"]), []).append(float(r[metric]))
    return {k: np.array(v) for k, v in out.items()}


def mark(proposed, other, lower_is_better):
    """Wilcoxon rank-sum at 0.05, as in the paper: '+' if the proposed algorithm is significantly better
    than `other`, '-' if significantly worse, '=' otherwise."""
    if len(proposed) < 2 or len(other) < 2 or ranksums(proposed, other).pvalue >= 0.05:
        return "="
    better = np.median(proposed) < np.median(other) if lower_is_better else np.median(proposed) > np.median(other)
    return "+" if better else "-"


def improvement(value, base):
    return f"{value:.4f}({(1 - value / base) * 100:.1f})" if value < base else f"{value:.4f}(-)"


def table_iv(data, problems, algorithms):
    """MIGD averaged over the three configurations, next to the paper's NSGA-II results."""
    lines = ["| Prob | Paper DA-NSGA-II | Paper ISVM-NSGA-II | " + " | ".join(algorithms) + " |",
             "|---" * (3 + len(algorithms)) + "|"]
    for p in problems:
        avg = {a: np.mean([data[(p, nt, tt, a)].mean() for nt, tt in CONFIGS if (p, nt, tt, a) in data])
               for a in algorithms}
        da, isvm = PAPER_TABLE_IV[p]
        cells = [f"{avg[a]:.4f}" if a == "random" else improvement(avg[a], avg["random"]) for a in algorithms]
        lines.append(f"| DF{p} | {da:.4f} | {improvement(isvm, da)} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def table_per_config(data, problems, algorithms, lower_is_better):
    """Mean ± std per problem and configuration, best in bold, Wilcoxon marks against the proposed method."""
    lines = ["| Prob | (nt, taut) | " + " | ".join(algorithms) + " |", "|---" * (2 + len(algorithms)) + "|"]
    for p in problems:
        for nt, tt in CONFIGS:
            if not all((p, nt, tt, a) in data for a in algorithms):
                continue
            means = {a: data[(p, nt, tt, a)].mean() for a in algorithms}
            best = (min if lower_is_better else max)(means, key=means.get)
            cells = []
            for a in algorithms:
                v = data[(p, nt, tt, a)]
                cell = f"{v.mean():.4f}±{v.std():.1e}"
                if a != PROPOSED:
                    cell += f"({mark(data[(p, nt, tt, PROPOSED)], v, lower_is_better)})"
                cells.append(f"**{cell}**" if a == best else cell)
            lines.append(f"| DF{p} | ({nt},{tt}) | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def igd_figure(rows, problems, algorithms, path):
    """IGD per environment for (nt, taut) = (10, 10), averaged over runs (paper Fig. 4)."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=5, cols=3, subplot_titles=[f"DF{p}" for p in problems])
    colors = dict(zip(ALGORITHMS, ["#7f7f7f", "#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]))
    for i, p in enumerate(problems):
        for a in algorithms:
            curves = [json.loads(r["igd"]) for r in rows
                      if int(r["problem"]) == p and (int(r["nt"]), int(r["taut"])) == (10, 10) and r["algorithm"] == a]
            if curves:
                fig.add_trace(go.Scatter(y=np.log10(np.mean(curves, axis=0)), name=a, legendgroup=a,
                                         showlegend=i == 0, line=dict(color=colors[a])),
                              row=i // 3 + 1, col=i % 3 + 1)
    fig.update_layout(height=1400, title="log10(IGD) per environment, (nt, τt) = (10, 10)")
    fig.write_html(path)


def build_tables(rows, metric):
    problems = sorted({int(r["problem"]) for r in rows})
    present = {r["algorithm"] for r in rows}
    main = [a for a in MAIN if a in present]
    migd, mhv = collect(rows, metric), collect(rows, "mhv")
    counts = [len(v) for v in migd.values()]
    parts = [f"Runs per cell: {min(counts)}-{max(counts)}. MIGD = `{metric}`. Marks: Wilcoxon rank-sum (0.05) of "
             f"{PROPOSED} against each column: + better, = no difference, - worse.",
             "## MIGD averaged over configurations (paper Table IV); % improvement vs random in parentheses",
             table_iv(migd, problems, main),
             "## MIGD per configuration (paper Table I)", table_per_config(migd, problems, main, True),
             "## MHV per configuration (paper Table II)", table_per_config(mhv, problems, main, False)]
    ablation = [a for a in ABLATION if a in present]
    if len(ablation) > len(main):
        parts += ["## Ablation, MIGD averaged over configurations (paper Table III)",
                  table_iv(migd, problems, ablation)]
    return "\n\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["run", "tables"])
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--problems", type=int, nargs="+", default=list(range(1, 15)))
    parser.add_argument("--algorithms", nargs="+", default=MAIN, choices=list(ALGORITHMS))
    parser.add_argument("--changes", type=int, default=30)
    parser.add_argument("--metric", default="migd_every_gen", choices=["migd_every_gen", "migd"])
    parser.add_argument("--csv", type=Path, default=OUT / "isvm_benchmark.csv")
    args = parser.parse_args()

    if args.command == "run":
        run_benchmark(args.csv, args.runs, args.workers, args.problems, args.algorithms, args.changes)
    else:
        rows = read_rows(args.csv)
        markdown = build_tables(rows, args.metric)
        (args.csv.parent / "isvm_tables.md").write_text(markdown, encoding="utf-8")
        igd_figure(rows, sorted({int(r["problem"]) for r in rows}), [a for a in ALGORITHMS if a in
                   {r["algorithm"] for r in rows}], args.csv.parent / "igd_curves.html")
        print(markdown)


if __name__ == "__main__":
    main()
