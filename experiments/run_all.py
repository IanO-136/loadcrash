"""Run every experiment in the paper and write CSVs to results/.

    python experiments/run_all.py            # full run
    python experiments/run_all.py --quick    # smoke run with few seeds
"""
import argparse
import csv
import itertools
import multiprocessing as mp
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from loadcrash.fuzz import calibrate, kill_trial  # noqa: E402
from loadcrash.harness import run_trial  # noqa: E402
from loadcrash.patterns import ALL, BY_NAME  # noqa: E402
from loadcrash.source import WorkloadConfig  # noqa: E402

OUT = os.path.join(ROOT, "results")


def write(name, rows):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path} ({len(rows)} rows)")


# E1
def _e1(args):
    pname, cp, rnd, seed = args
    return run_trial(BY_NAME[pname], WorkloadConfig(seed=seed), crash_point=cp, crash_round=rnd).row()


def e1(seeds, pool):
    """Systematic crash-point enumeration on an ordered source (no commit lag)."""
    jobs = [(P.name, cp, rnd, s) for P in ALL for cp in P.crash_points
            for rnd in (2, 5, 10, 15, 20) for s in range(seeds)]
    write("e1_crash_points.csv", pool.map(_e1, jobs, chunksize=8))


# E2
E2_PREDICATES = [("gt", 0), ("gte", 0)] + [("lookback", L) for L in (2, 5, 10, 15, 20)]
E2_LAGS = (0.0, 0.01, 0.02, 0.05, 0.1, 0.2)


def _e2(args):
    pname, pred, L, p_lag, seed = args
    return run_trial(BY_NAME[pname], WorkloadConfig(seed=seed, p_lag=p_lag),
                     predicate=pred, lookback=L).row()


def e2(seeds, pool):
    """Extraction predicate x source commit lag, no crashes."""
    jobs = [(p, pred, L, lag, s) for p in ("A4", "M2", "P2", "F2")
            for (pred, L) in E2_PREDICATES for lag in E2_LAGS for s in range(seeds)]
    write("e2_watermark_lag.csv", pool.map(_e2, jobs, chunksize=8))


# E3
def _e3(args):
    pname, cp, pred, L, seed = args
    return run_trial(BY_NAME[pname], WorkloadConfig(seed=seed, p_lag=0.05), predicate=pred,
                     lookback=L, crash_point=cp, crash_round=10).row()


def e3(seeds, pool):
    """Crashes AND late data together: do the two fixes compose?"""
    combos = [("A4", "gt", 0), ("A4", "lookback", 15), ("M2", "gt", 0), ("M2", "lookback", 15),
              ("M1", "lookback", 15), ("A1", "lookback", 15), ("P2", "gt", 0), ("P2", "lookback", 15)]
    jobs = [(p, cp, pred, L, s) for (p, pred, L) in combos
            for cp in [None] + BY_NAME[p].crash_points for s in range(seeds)]
    write("e3_crash_and_lag.csv", pool.map(_e3, jobs, chunksize=8))


# E4
FUZZ_W = WorkloadConfig(rounds=5, ticks_per_round=20, txns_per_tick=25, seed=0)


def _e4(args):
    pname, seed, est = args
    w = WorkloadConfig(**{**FUZZ_W.__dict__, "seed": seed})
    return kill_trial(pname, seed, w, kill_round=3, run_estimate_s=est).row()


def e4(kills, pool):
    """Real SIGKILL at a uniformly random instant during one pipeline run."""
    est = {P.name: calibrate(P.name, FUZZ_W) * 1.05 for P in ALL}
    print("  calibrated run times (s):", {k: round(v, 4) for k, v in est.items()})
    jobs = [(P.name, s, est[P.name]) for P in ALL for s in range(kills)]
    write("e4_sigkill.csv", pool.map(_e4, jobs, chunksize=4))


# E5
def _e5(args):
    pname, guard, sp, rnd, seed = args
    return run_trial(BY_NAME[pname], WorkloadConfig(seed=seed), guard=guard,
                     stall_point=sp, stall_round=rnd).row()


def zombie_points(P):
    # skip points inside an open write transaction (SQLite has one writer, so B would just
    # block) and the final point (nothing left for A to do)
    return [cp for cp in P.crash_points[:-1] if not cp.startswith("mid_")]


def e5(seeds, pool):
    """A stalled run wakes up after its replacement finished."""
    sql = ["A1", "A2", "A4", "M1", "M2", "P1", "P2"]
    files = ["F1", "F2", "F4"]
    jobs = [(p, g, sp, rnd, s) for p in sql for g in ("none", "monotonic", "cas")
            for sp in zombie_points(BY_NAME[p]) for rnd in (5, 10, 15) for s in range(seeds)]
    jobs += [(p, "none", sp, rnd, s) for p in files
             for sp in zombie_points(BY_NAME[p]) for rnd in (5, 10, 15) for s in range(seeds)]
    write("e5_zombie.csv", pool.map(_e5, jobs, chunksize=8))


# E5b: the same zombie interleavings with commit-horizon extraction and Pareto lag
def _e5b(args):
    pname, guard, rnd, seed = args
    w = WorkloadConfig(seed=seed, p_lag=0.1, lag_dist="pareto", rounds=20)
    return run_trial(BY_NAME[pname], w, predicate="horizon", guard=guard,
                     stall_point="after_extract", stall_round=rnd,
                     cooldown_rounds=w.lag_cap // w.ticks_per_round + 1).row()


def e5b(seeds, pool):
    jobs = [(p, g, rnd, s) for p in ("A4", "M2", "P2") for g in ("none", "monotonic", "cas")
            for rnd in (5, 10, 15) for s in range(seeds)]
    jobs += [("F4", "none", rnd, s) for rnd in (5, 10, 15) for s in range(seeds)]
    write("e5b_zombie_horizon.csv", pool.map(_e5b, jobs, chunksize=4))


# E6
E6_STRATEGIES = [("M2", "gt", 0), ("M2", "lookback", 15), ("M2", "lookback", 30),
                 ("M2", "lookback", 60), ("M2A", "gt", 0), ("M2", "horizon", 0), ("A4", "horizon", 0)]


def _e6(args):
    pname, pred, L, dist, p_lag, seed = args
    w = WorkloadConfig(seed=seed, p_lag=p_lag, lag_dist=dist, rounds=40)
    r = run_trial(BY_NAME[pname], w, predicate=pred, lookback=L,
                  cooldown_rounds=w.lag_cap // w.ticks_per_round + 1, track_latency=True).row()
    r["lag_dist"] = dist
    return r


def e6(seeds, pool):
    """Watermark strategies under bounded and heavy-tailed commit lag."""
    jobs = [(p, pred, L, d, lag, s) for (p, pred, L) in E6_STRATEGIES
            for d in ("uniform", "lognormal", "pareto") for lag in (0.02, 0.1) for s in range(seeds)]
    write("e6_strategies.csv", pool.map(_e6, jobs, chunksize=4))


# E7
def _e7(args):
    pname, cp, rnd, seed = args
    w = WorkloadConfig(seed=seed, p_lag=0.1, lag_dist="pareto", rounds=40)
    r = run_trial(BY_NAME[pname], w, predicate="horizon", crash_point=cp, crash_round=rnd,
                  cooldown_rounds=w.lag_cap // w.ticks_per_round + 1).row()
    return r


def e7(seeds, pool):
    """Horizon extraction plus crashes, on targets with no key."""
    jobs = [(p, cp, rnd, s) for p in ("A4", "F2", "F4") for cp in BY_NAME[p].crash_points
            for rnd in (10, 20, 30) for s in range(seeds)]
    write("e7_horizon_crash.csv", pool.map(_e7, jobs, chunksize=4))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only", default="e1,e2,e3,e4,e5,e5b,e6,e7")
    a = ap.parse_args()
    seeds, kills = (2, 10) if a.quick else (10, 200)
    with mp.Pool(max(2, os.cpu_count() or 2)) as pool:
        for name in a.only.split(","):
            t = time.time()
            print(f"[{name}]")
            {"e1": e1, "e2": e2, "e3": e3, "e5": e5, "e5b": e5b, "e6": e6, "e7": e7}.get(name, lambda s, p: None)(seeds, pool)
            if name == "e4":
                e4(kills, pool)
            print(f"  {time.time() - t:.0f}s")
