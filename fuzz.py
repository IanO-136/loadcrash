"""SIGKILL fuzzing with real processes.

The harness fakes crashes by raising an exception at a named point. Here we
check that against the real thing: run one pipeline run in a child process and
kill -9 it at a random moment, which can land mid-write or inside SQLite's
commit. The child prints every crash point it passes, so afterwards we know
the last one it reached.
"""
from __future__ import annotations

import os
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass

from .patterns import BY_NAME, Corrupt, Ctx
from .source import SourceDB, WorkloadConfig, generate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def child_main(argv):
    pattern_name, workdir, source_path, predicate, lookback = argv
    pattern = BY_NAME[pattern_name]()

    class TracingCtx(Ctx):
        def cp(self, name):
            sys.stdout.write(name + "\n")
            sys.stdout.flush()

    ctx = TracingCtx(source_path=source_path, workdir=workdir, predicate=predicate,
                     lookback=int(lookback))
    sys.stdout.write("GO\n")
    sys.stdout.flush()
    t0 = time.perf_counter()
    pattern.run(ctx)
    sys.stdout.write(f"DONE {time.perf_counter() - t0:.6f}\n")
    sys.stdout.flush()


def _spawn(pattern, workdir, src_path, predicate="gt", lookback=0):
    return subprocess.Popen(
        [sys.executable, "-m", "loadcrash.fuzz", pattern, workdir, src_path, predicate, str(lookback)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)


@dataclass
class KillResult:
    pattern: str
    seed: int
    delay_s: float
    run_s: float
    killed: bool
    last_cp: str
    lost: int = 0
    duplicates: int = 0
    corrupt_final: bool = False
    stuck: bool = False
    exp_duplicates: int = 0
    exp_regression: int = 0
    exp_corrupt: bool = False

    @property
    def final_ok(self):
        return not (self.lost or self.duplicates or self.corrupt_final or self.stuck)

    def row(self):
        d = asdict(self)
        d["final_ok"] = self.final_ok
        return d


def kill_trial(pattern_name: str, seed: int, wcfg: WorkloadConfig, kill_round: int = 3,
               run_estimate_s: float = 0.05) -> KillResult:
    pattern = BY_NAME[pattern_name]()
    rng = random.Random(seed * 7919 + sum(map(ord, pattern_name)))
    workdir = tempfile.mkdtemp(prefix=f"lk_{pattern_name}_")
    src = SourceDB(os.path.join(workdir, "source.db"), generate(wcfg))
    pattern.setup(workdir)
    res = KillResult(pattern_name, seed, 0.0, 0.0, False, "")
    try:
        for r in range(1, wcfg.rounds + 1):
            src.advance_to(r * wcfg.ticks_per_round)
            if r != kill_round:
                pattern.run(Ctx(source_path=src.path, workdir=workdir))
                continue
            before = set(pattern.read_view(workdir))
            delay = rng.uniform(0, run_estimate_s)
            res.delay_s = delay
            p = _spawn(pattern_name, workdir, src.path)
            assert p.stdout.readline().strip() == "GO"
            time.sleep(delay)
            p.send_signal(signal.SIGKILL)
            out = p.stdout.read().split()
            p.wait()
            cps = [x for x in out if x and not x.replace(".", "").isdigit()]
            res.killed = "DONE" not in out
            if not res.killed:
                res.run_s = float(out[out.index("DONE") + 1])
            res.last_cp = ([c for c in cps if c != "DONE"] or ["<start>"])[-1]
            try:
                v = pattern.read_view(workdir)
                res.exp_duplicates = len(v) - len(set(v))
                res.exp_regression = len(before - set(v))
            except Corrupt:
                res.exp_corrupt = True
            try:  # orchestrator retry
                pattern.run(Ctx(source_path=src.path, workdir=workdir))
            except Corrupt:
                res.stuck = True
                break
        if not res.stuck:
            src.advance_to(10**9)
            pattern.run(Ctx(source_path=src.path, workdir=workdir))
        oracle = src.all_ids()
        try:
            v = pattern.read_view(workdir)
            res.lost = len(oracle - set(v))
            res.duplicates = len(v) - len(set(v))
        except Corrupt:
            res.corrupt_final = True
    finally:
        src.close()
        shutil.rmtree(workdir, ignore_errors=True)
    return res


def calibrate(pattern_name: str, wcfg: WorkloadConfig, kill_round: int = 3, n: int = 5) -> float:
    """Median wall time of the kill-round run, measured inside a child process."""
    times = []
    for i in range(n):
        workdir = tempfile.mkdtemp(prefix="lcal_")
        src = SourceDB(os.path.join(workdir, "source.db"), generate(wcfg))
        pattern = BY_NAME[pattern_name]()
        pattern.setup(workdir)
        for r in range(1, kill_round + 1):
            src.advance_to(r * wcfg.ticks_per_round)
            if r < kill_round:
                pattern.run(Ctx(source_path=src.path, workdir=workdir))
        p = _spawn(pattern_name, workdir, src.path)
        out = p.stdout.read().split()
        p.wait()
        times.append(float(out[out.index("DONE") + 1]))
        src.close()
        shutil.rmtree(workdir, ignore_errors=True)
    times.sort()
    return times[len(times) // 2]


if __name__ == "__main__":
    child_main(sys.argv[1:])
