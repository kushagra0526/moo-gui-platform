#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from types import SimpleNamespace
from gui.callbacks.prediction_callbacks import STRATEGIES, compare, new_progress, render

TINY = {"problem": 2, "changes": 2, "taut": 3, "nt": 10, "pop_size": 20}


class TestPredictionPage(unittest.TestCase):

    def test_comparison_runs_all_three_and_renders(self):
        app = SimpleNamespace()
        progress = app._pred = new_progress(dict(TINY))
        compare(app, progress)
        self.assertFalse(progress["running"])
        self.assertIsNone(progress["error"])
        self.assertEqual(list(progress["summary"]), [key for key, _, _ in STRATEGIES])
        self.assertTrue(all(len(c) == 3 for c in progress["curves"].values()))
        fig, table, status = render(progress)
        self.assertEqual(len(fig.data), 3)
        self.assertIn("%", str(table))  # ISVM rows show their change against random restart

    def test_stop_and_replacement_end_the_comparison(self):
        app = SimpleNamespace()
        progress = app._pred = new_progress(dict(TINY))
        progress["stop"] = True
        compare(app, progress)
        self.assertEqual(progress["summary"], {})
        self.assertEqual(list(progress["curves"]), ["random"])  # stopped after its first environment

        old = new_progress(dict(TINY))
        app._pred = new_progress(dict(TINY))  # a newer comparison started
        compare(app, old)
        self.assertEqual(old["summary"], {})
        self.assertFalse(old["running"])


if __name__ == "__main__":
    unittest.main()
