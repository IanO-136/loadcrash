"""Fake OLTP source where transactions can commit late.

The source table is insert-only (think payments or clicks):

    events(event_id INTEGER PRIMARY KEY, ts INTEGER, payload INTEGER)

A transaction gets its ts when it starts, like DEFAULT now() in Postgres, but
nobody can read its rows until it commits. With probability p_lag it commits
1..max_lag ticks late. That means a row can show up with a ts older than rows
we already extracted, which is how high-watermark extraction loses data.
p_lag = 0 gives a perfectly ordered source.
"""
from __future__ import annotations

import math
import random
import sqlite3
from dataclasses import dataclass, field


@dataclass
class Txn:
    ts: int            # start time, written into every row's ts column
    visible_at: int    # commit time; readers cannot see rows before this
    rows: list[tuple[int, int, int]] = field(default_factory=list)  # (event_id, ts, payload)


@dataclass
class WorkloadConfig:
    rounds: int = 20            # number of scheduled pipeline runs
    ticks_per_round: int = 10   # source clock ticks between pipeline runs
    txns_per_tick: float = 3.0  # Poisson mean
    max_rows_per_txn: int = 4
    p_lag: float = 0.0          # probability a txn commits late
    max_lag: int = 15           # ticks, for lag_dist == "uniform"
    seed: int = 0
    lag_dist: str = "uniform"   # uniform | lognormal | pareto
    lag_median: float = 4.0     # lognormal: median lag in ticks
    lag_sigma: float = 1.0      # lognormal: spread
    pareto_alpha: float = 1.2   # pareto: tail index (smaller = heavier tail)
    lag_cap: int = 300          # no transaction stays open longer than this


def _sample_lag(rng: random.Random, cfg: WorkloadConfig) -> int:
    if cfg.lag_dist == "uniform":
        return rng.randint(1, cfg.max_lag)
    if cfg.lag_dist == "lognormal":
        x = rng.lognormvariate(math.log(cfg.lag_median), cfg.lag_sigma)
    elif cfg.lag_dist == "pareto":
        x = rng.paretovariate(cfg.pareto_alpha)
    else:
        raise ValueError(cfg.lag_dist)
    return min(cfg.lag_cap, max(1, math.ceil(x)))


def generate(cfg: WorkloadConfig) -> list[Txn]:
    """Deterministically generate the full list of source transactions."""
    rng = random.Random(cfg.seed)
    txns: list[Txn] = []
    next_id = 1
    total_ticks = cfg.rounds * cfg.ticks_per_round
    for tick in range(1, total_ticks + 1):
        # Poisson sample, done by hand so everything comes from one seeded RNG
        k, p, l = 0, 1.0, pow(2.718281828459045, -cfg.txns_per_tick)
        while True:
            p *= rng.random()
            if p <= l:
                break
            k += 1
        for _ in range(k):
            lag = _sample_lag(rng, cfg) if rng.random() < cfg.p_lag else 0
            t = Txn(ts=tick, visible_at=tick + lag)
            for _ in range(rng.randint(1, cfg.max_rows_per_txn)):
                t.rows.append((next_id, tick, rng.randint(1, 10_000)))
                next_id += 1
            txns.append(t)
    return txns


class SourceDB:
    """SQLite-backed source that applies transactions as they become visible."""

    def __init__(self, path: str, txns: list[Txn]):
        self.path = path
        self.pending = sorted(txns, key=lambda t: (t.visible_at, t.ts))
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS events("
            "event_id INTEGER PRIMARY KEY, ts INTEGER NOT NULL, payload INTEGER NOT NULL)"
        )
        self.conn.execute("CREATE INDEX IF NOT EXISTS ix_ts ON events(ts)")
        # Stand-in for pg_snapshot_xmin(): start time of the oldest transaction still open.
        self.conn.execute("CREATE TABLE IF NOT EXISTS horizon(v INTEGER)")
        self.conn.execute("INSERT INTO horizon VALUES (1)")
        self.conn.commit()
        self.now = 0
        self.commit_time = {r[0]: t.visible_at for t in txns for r in t.rows}

    def advance_to(self, t: int) -> int:
        """Commit every transaction whose commit time is <= t. Returns #rows applied."""
        n = 0
        while self.pending and self.pending[0].visible_at <= t:
            txn = self.pending.pop(0)
            self.conn.executemany("INSERT INTO events VALUES (?,?,?)", txn.rows)
            n += len(txn.rows)
        still_open = [x.ts for x in self.pending if x.ts <= t]
        self.conn.execute("UPDATE horizon SET v=?", (min(still_open) if still_open else t + 1,))
        self.conn.commit()
        self.now = t
        return n

    def all_ids(self) -> set[int]:
        return {r[0] for r in self.conn.execute("SELECT event_id FROM events")}

    def close(self):
        self.conn.close()
