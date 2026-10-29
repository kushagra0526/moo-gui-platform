#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
import numpy as np
from dmoea import run, igd, hv, smote, loras, training_set, ISVMPredictor
from cec2018_dmop import true_front


class TestOversampling(unittest.TestCase):

    def setUp(self):
        self.rng = np.random.default_rng(0)
        self.P = self.rng.random((12, 4))

    def test_smote_points_lie_on_segments_between_neighbours(self):
        S = smote(self.P, r=3, k=2, rng=self.rng)
        self.assertEqual(S.shape, (36, 4))
        def on_segment(s, base, q):
            g = np.dot(s - base, q - base) / np.dot(q - base, q - base)
            return 0 <= g <= 1 and np.allclose(base + g * (q - base), s)

        for i, s in enumerate(S):
            base = self.P[i // 3]
            self.assertTrue(any(on_segment(s, base, q) for q in self.P if not np.array_equal(q, base)))

    def test_loras_stays_near_its_neighbourhood(self):
        L = loras(self.P, r=5, k=3, rng=self.rng, sigma=0.005)
        self.assertEqual(L.shape, (60, 4))
        # convex combinations of noisy copies cannot leave the data's bounding box by more than the noise
        self.assertTrue(np.all(L >= self.P.min(0) - 0.05) and np.all(L <= self.P.max(0) + 0.05))

    def test_single_solution_still_oversamples(self):
        one = self.P[:1]
        self.assertTrue(np.allclose(smote(one, 4, 5, self.rng), one))
        self.assertTrue(np.allclose(loras(one, 4, 5, self.rng), one, atol=0.05))

    def test_training_set_is_balanced_and_in_unit_cube(self):
        xl, xu = np.full(4, -2.0), np.full(4, 3.0)
        X, y = training_set(xl + self.P * (xu - xl), xl, xu, "loras", r=5, k=5, rng=self.rng)
        self.assertEqual(np.sum(y > 0), 12 * 6)
        self.assertEqual(np.sum(y < 0), 12 * 6)
        self.assertTrue(np.all((X >= 0) & (X <= 1)))


class TestPredictor(unittest.TestCase):

    def test_predicted_population_comes_from_the_positive_region(self):
        rng = np.random.default_rng(1)
        X = rng.random((400, 2))
        y = np.where(np.linalg.norm(X - 0.5, axis=1) < 0.2, 1.0, -1.0)
        p = ISVMPredictor(C=10.0, gamma=10.0)
        p.update(X, y)
        pts, found, draws = p.predict_population(30, rng)
        self.assertEqual(pts.shape, (30, 2))
        self.assertGreater(found, 30)
        self.assertLess(np.mean(np.linalg.norm(pts - 0.5, axis=1)), 0.3)

    def test_history_carries_support_vectors(self):
        rng = np.random.default_rng(2)
        X = rng.random((100, 2)); y = np.where(X[:, 0] > 0.5, 1.0, -1.0)
        p = ISVMPredictor(C=1.0, gamma=1.0)
        p.update(X, y)
        kept = len(p.X)
        p.update(X + 0.0, y)
        self.assertLessEqual(len(p.X), kept + len(X))
        self.assertGreater(len(p.svm.support_vectors_), 0)


class TestMetricsAndRun(unittest.TestCase):

    def test_metrics(self):
        pf = true_front(2, 0.3, 200)
        self.assertEqual(igd(pf, pf), 0.0)
        self.assertGreater(hv(pf, pf), hv(pf + 0.05, pf))

    def test_short_runs_are_deterministic(self):
        kwargs = dict(nt=10, taut=3, n_changes=2, pop_size=20, C=1.0, gamma=1.0, seed=3)
        for strategy in ("random", "isvm"):
            a = run(2, strategy=strategy, **kwargs)
            self.assertEqual(len(a["igd"]), 3)
            self.assertTrue(np.isfinite(a["migd"]) and np.isfinite(a["mhv"]))
            self.assertEqual(a["migd"], run(2, strategy=strategy, **kwargs)["migd"])
        self.assertEqual(len(a["acceptance"]), 2)

    def test_no_reaction_and_stopping_from_the_hook(self):
        seen = []
        r = run(2, strategy="none", nt=10, taut=3, n_changes=5, pop_size=20, seed=3,
                on_environment=lambda info: seen.append(info["env"]) or info["env"] == 1)
        self.assertEqual(seen, [0, 1])
        self.assertEqual(len(r["igd"]), 2)


if __name__ == "__main__":
    unittest.main()
