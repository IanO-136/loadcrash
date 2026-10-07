"""Sanity tests. Run with: python -m unittest discover -s tests"""
import unittest

from loadcrash.harness import run_trial
from loadcrash.patterns import ALL, BY_NAME
from loadcrash.source import WorkloadConfig, generate

W = WorkloadConfig(rounds=6, seed=3)


class TestBaseline(unittest.TestCase):
    def test_every_pattern_is_correct_without_faults(self):
        for P in ALL:
            r = run_trial(P, W)
            self.assertTrue(r.final_ok, f"{P.name}: {r}")
            self.assertGreater(r.source_rows, 0)

    def test_generator_is_deterministic(self):
        a = [(t.ts, t.visible_at, t.rows) for t in generate(W)]
        b = [(t.ts, t.visible_at, t.rows) for t in generate(W)]
        self.assertEqual(a, b)

    def test_every_crash_point_is_reachable(self):
        for P in ALL:
            for cp in P.crash_points:
                r = run_trial(P, W, crash_point=cp, crash_round=3)
                self.assertTrue(r.crash_fired, f"{P.name}/{cp}")


class TestKnownOutcomes(unittest.TestCase):
    def test_append_then_wm_duplicates(self):
        r = run_trial(BY_NAME["A1"], W, crash_point="after_data_commit", crash_round=3)
        self.assertGreater(r.duplicates, 0)
        self.assertEqual(r.lost, 0)

    def test_wm_then_append_loses(self):
        r = run_trial(BY_NAME["A2"], W, crash_point="after_wm_commit", crash_round=3)
        self.assertGreater(r.lost, 0)

    def test_sqlite_txn_is_atomic(self):
        for name in ["A4", "M2", "P2"]:
            r = run_trial(BY_NAME[name], W, crash_point="mid_txn", crash_round=3)
            self.assertTrue(r.final_ok and r.transient_ok, name)

    def test_inplace_manifest_bricks_table(self):
        r = run_trial(BY_NAME["F3"], W, crash_point="mid_manifest_write", crash_round=3)
        self.assertTrue(r.stuck and r.corrupt_final)

    def test_strict_watermark_loses_late_rows(self):
        w = WorkloadConfig(rounds=10, p_lag=0.2, seed=1)
        self.assertGreater(run_trial(BY_NAME["M2"], w, predicate="gt").lost, 0)
        self.assertEqual(run_trial(BY_NAME["M2"], w, predicate="lookback", lookback=w.max_lag).lost, 0)


class TestNewMechanisms(unittest.TestCase):
    W = WorkloadConfig(rounds=12, p_lag=0.1, lag_dist="pareto", seed=2)

    def test_horizon_is_exact_even_for_append(self):
        for name in ["A4", "M2", "F2"]:
            r = run_trial(BY_NAME[name], self.W, predicate="horizon")
            self.assertTrue(r.final_ok, name)
            self.assertEqual(r.rows_read, r.source_rows, name)

    def test_monotonic_guard_makes_zombie_overwrite_permanent(self):
        r = run_trial(BY_NAME["P2"], W, guard="monotonic", stall_point="after_extract", stall_round=3)
        self.assertTrue(r.zombie_fired)
        self.assertGreater(r.lost, 0)
        r = run_trial(BY_NAME["P2"], W, guard="none", stall_point="after_extract", stall_round=3)
        self.assertEqual(r.lost, 0)

    def test_cas_fences_atomic_patterns_only(self):
        r = run_trial(BY_NAME["A4"], W, guard="cas", stall_point="after_extract", stall_round=3)
        self.assertTrue(r.zombie_fenced and r.final_ok)
        r = run_trial(BY_NAME["A1"], W, guard="cas", stall_point="after_extract", stall_round=3)
        self.assertTrue(r.zombie_fenced)
        self.assertGreater(r.duplicates, 0)

    def test_versioned_log_fences_zombie(self):
        r = run_trial(BY_NAME["F4"], W, stall_point="after_extract", stall_round=3)
        self.assertTrue(r.zombie_fenced and r.final_ok)


if __name__ == "__main__":
    unittest.main()
