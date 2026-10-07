"""Runs one trial: push a pattern through the workload, maybe crash it, then check the result."""
from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import asdict, dataclass

import threading

from .patterns import Corrupt, Crash, Ctx, Fenced, Pattern
from .source import SourceDB, WorkloadConfig, generate


@dataclass
class TrialResult:
    pattern: str
    crash_point: str | None
    crash_round: int | None
    predicate: str
    lookback: int
    p_lag: float
    seed: int
    source_rows: int = 0
    # final state, after retry and drain runs
    lost: int = 0               # source rows absent from the consumer view
    duplicates: int = 0         # extra copies visible to consumers
    phantoms: int = 0           # rows in view that never existed in source (sanity)
    corrupt_final: bool = False  # consumer view unreadable at the end
    stuck: bool = False          # pipeline itself could no longer run
    storage_overhead: int = 0    # physical rows beyond one per source row
    rows_read: int = 0           # total rows pulled from source (cost)
    rows_read_sched: int = 0     # same, counted only over the scheduled runs
    # transient state, observed by a reader between the crash and the retry
    exp_duplicates: int = 0
    exp_regression: int = 0      # rows a reader could see before the run but not after the crash
    exp_corrupt: bool = False
    crash_fired: bool = False
    # zombie runs: run A stalls, a replacement run B finishes, then A wakes up
    guard: str = "none"
    stall_point: str | None = None
    zombie_fired: bool = False
    zombie_fenced: bool = False
    zombie_error: str = ""
    # freshness: ticks from a row's commit in the source to its first appearance downstream
    lat_mean: float = 0.0
    lat_p50: float = 0.0
    lat_p99: float = 0.0
    lat_max: float = 0.0

    @property
    def final_ok(self) -> bool:
        return not (self.lost or self.duplicates or self.phantoms or self.corrupt_final or self.stuck)

    @property
    def transient_ok(self) -> bool:
        return not (self.exp_duplicates or self.exp_regression or self.exp_corrupt)

    def row(self) -> dict:
        d = asdict(self)
        d["final_ok"] = self.final_ok
        d["transient_ok"] = self.transient_ok
        return d


def _pct(xs, q):
    if not xs:
        return 0.0
    xs = sorted(xs)
    return float(xs[min(len(xs) - 1, int(q * len(xs)))])


def run_trial(pattern_cls: type[Pattern], wcfg: WorkloadConfig, *, predicate: str = "gt",
              lookback: int = 0, crash_point: str | None = None, crash_round: int | None = None,
              guard: str = "none", stall_point: str | None = None, stall_round: int | None = None,
              cooldown_rounds: int = 0, track_latency: bool = False,
              drain_runs: int = 2, keep_dir: bool = False) -> TrialResult:
    pattern = pattern_cls()
    res = TrialResult(pattern.name, crash_point, crash_round, predicate, lookback, wcfg.p_lag,
                      wcfg.seed, guard=guard, stall_point=stall_point)
    workdir = tempfile.mkdtemp(prefix=f"lc_{pattern.name}_")
    src = SourceDB(os.path.join(workdir, "source.db"), generate(wcfg))
    pattern.setup(workdir)
    seen: set[int] = set()
    latencies: list[int] = []

    def mk_ctx(crash=None):
        return Ctx(source_path=src.path, workdir=workdir, predicate=predicate,
                   lookback=lookback, crash_at=crash, guard=guard)

    def one_run(crash=None) -> bool:
        """One pipeline run. False if it crashed."""
        ctx = mk_ctx(crash)
        try:
            pattern.run(ctx)
            return True
        except Crash:
            return False
        finally:
            res.rows_read += ctx.rows_read

    def note_arrivals():
        if not track_latency:
            return
        try:
            now = set(pattern.read_view(workdir))
        except Corrupt:
            return
        for i in now - seen:
            if i in src.commit_time:
                latencies.append(src.now - src.commit_time[i])
        seen.update(now)

    def zombie_round(r):
        """Run A stalls at stall_point. The orchestrator gives up on it, time moves on,
        and replacement run B goes through. Then A wakes up and finishes what it started."""
        stalled, resume = threading.Event(), threading.Event()
        hit = []

        def on_cp(name):
            if name == stall_point and not hit:
                hit.append(name)
                stalled.set()
                resume.wait(60)

        ctx_a = mk_ctx()
        ctx_a.on_cp = on_cp
        outcome = {}

        def run_a():
            try:
                pattern.run(ctx_a)
            except Fenced:
                outcome["fenced"] = True
            except Exception as e:  # A tripped over something B changed; it just dies
                outcome["error"] = type(e).__name__

        t = threading.Thread(target=run_a)
        t.start()
        while t.is_alive() and not stalled.is_set():
            stalled.wait(0.005)
        if hit:
            res.zombie_fired = True
            src.advance_to((r + 1) * wcfg.ticks_per_round)
            one_run()  # B
            resume.set()
        t.join()
        res.rows_read += ctx_a.rows_read
        res.zombie_fenced = bool(outcome.get("fenced"))
        res.zombie_error = outcome.get("error", "")

    try:
        last = wcfg.rounds + cooldown_rounds
        schedule = list(range(1, last + 1)) + [None] * drain_runs
        for r in schedule:
            if res.stuck:
                break
            if r == wcfg.rounds + 1 or (r is None and not res.rows_read_sched):
                res.rows_read_sched = res.rows_read
            if r is None:  # drain: let every late transaction commit, then run again
                src.advance_to(10**9)
            else:
                src.advance_to(max(src.now, r * wcfg.ticks_per_round))

            if r is not None and r == stall_round and stall_point:
                zombie_round(r)
                note_arrivals()
                continue

            if r is not None and r == crash_round and crash_point:
                try:
                    before = set(pattern.read_view(workdir))
                except Corrupt:
                    before = set()
                if one_run(crash_point):
                    note_arrivals()
                    continue  # crash point not reached in this run (e.g. empty batch)
                res.crash_fired = True
                # a downstream reader looks at the table before the orchestrator retries
                try:
                    v = pattern.read_view(workdir)
                    res.exp_duplicates = len(v) - len(set(v))
                    res.exp_regression = len(before - set(v))
                except Corrupt:
                    res.exp_corrupt = True
            # normal run, or the orchestrator's retry of the crashed run
            try:
                one_run()
            except Corrupt:
                res.stuck = True
            if r is not None:
                note_arrivals()

        oracle = src.all_ids()
        res.source_rows = len(oracle)
        try:
            v = pattern.read_view(workdir)
            s = set(v)
            res.lost = len(oracle - s)
            res.duplicates = len(v) - len(s)
            res.phantoms = len(s - oracle)
            res.storage_overhead = pattern.storage_rows(workdir) - len(s & oracle)
        except Corrupt:
            res.corrupt_final = True
        if latencies:
            res.lat_mean = round(sum(latencies) / len(latencies), 3)
            res.lat_p50 = _pct(latencies, 0.5)
            res.lat_p99 = _pct(latencies, 0.99)
            res.lat_max = float(max(latencies))
    finally:
        src.close()
        if not keep_dir:
            shutil.rmtree(workdir, ignore_errors=True)
    return res
