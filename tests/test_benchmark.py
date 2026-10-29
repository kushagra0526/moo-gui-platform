#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import unittest
import numpy as np
from benchmarks.isvm_benchmark import CONFIGS, MAIN, build_tables, improvement, mark


class TestBenchmarkTables(unittest.TestCase):

    def setUp(self):
        rng = np.random.default_rng(0)
        level = {"random": 1.0, "isvm-smote": 0.5, "isvm-loras": 0.3}
        self.rows = [{"problem": "1", "nt": str(nt), "taut": str(tt), "algorithm": a, "seed": str(s),
                      "migd_every_gen": str(level[a] + rng.normal(0, 0.01)),
                      "mhv": str(1 - level[a] + rng.normal(0, 0.01)), "igd": json.dumps([level[a]] * 3)}
                     for nt, tt in CONFIGS for a in MAIN for s in range(8)]

    def test_marks_and_improvement(self):
        self.assertEqual(mark(np.full(8, 0.3) + np.arange(8) * 1e-3, np.full(8, 0.5), True), "+")
        self.assertEqual(mark(np.full(8, 0.3) + np.arange(8) * 1e-3, np.full(8, 0.5), False), "-")
        self.assertEqual(mark(np.array([0.3, 0.31]), np.array([0.5, 0.51]), True), "=")  # too few runs
        self.assertEqual(improvement(0.5, 1.0), "0.5000(50.0)")
        self.assertEqual(improvement(1.2, 1.0), "1.2000(-)")

    def test_tables(self):
        md = build_tables(self.rows, "migd_every_gen")
        self.assertIn("| DF1 | 0.5660 | 0.4381(22.6) |", md)  # paper Table IV row
        self.assertIn("(70.", md)                              # LoRAS ~70% better than random
        self.assertIn("(+)", md)
        self.assertNotIn("(-)", md.split("MHV")[0].split("Table I)")[1])  # LoRAS never worse on MIGD
        self.assertIn("Runs per cell: 8-8", md)


if __name__ == "__main__":
    unittest.main()
