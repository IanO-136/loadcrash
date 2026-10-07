"""The load patterns we test.

Each pattern does one pipeline run: read the watermark, pull new rows from the
source, write them, move the watermark forward. Patterns call ctx.cp(name) at
each step boundary so the harness can crash them there (in a normal run the
call does nothing). A crash means every open connection is closed without
committing, so SQLite throws away the open transaction, and any file keeps
whatever bytes had been written.

A* = append to a table with no unique key, M* = upsert on the primary key,
P* = rebuild whole time partitions, F* = data files in a directory.
"""
from __future__ import annotations

import glob
import json
import math
import os
import sqlite3
import uuid
from dataclasses import dataclass, field

PARTITION_WIDTH = 10  # ticks per partition ("day")


class Crash(Exception):
    """Raised by the harness to simulate the process dying at a crash point."""


class Fenced(Exception):
    """The watermark changed under us (another run got there first), so this run gives up."""


class Corrupt(Exception):
    """Raised by a reader when the target cannot be read (torn file etc.)."""


@dataclass
class Ctx:
    source_path: str
    workdir: str
    predicate: str = "gt"        # gt | gte | lookback
    lookback: int = 0            # ticks, for predicate == "lookback"
    crash_at: str | None = None  # crash point name, or None
    rows_read: int = 0
    guard: str = "none"          # none | monotonic | cas  (how the watermark is written)
    wm_override: int | None = None  # set by horizon extraction
    on_cp: object = None         # optional callback, used to stall a run (zombie tests)
    trace: list[str] = field(default_factory=list)

    def cp(self, name: str) -> None:
        self.trace.append(name)
        if self.on_cp is not None:
            self.on_cp(name)
        if self.crash_at == name:
            raise Crash(name)


def extract(ctx: Ctx, wm: int) -> list[tuple[int, int, int]]:
    src = sqlite3.connect(ctx.source_path)
    try:
        if ctx.predicate == "gt":
            q, arg = "SELECT event_id, ts, payload FROM events WHERE ts > ?", wm
        elif ctx.predicate == "gte":
            q, arg = "SELECT event_id, ts, payload FROM events WHERE ts >= ?", wm
        elif ctx.predicate == "lookback":
            q, arg = "SELECT event_id, ts, payload FROM events WHERE ts > ?", wm - ctx.lookback
        elif ctx.predicate == "horizon":
            # Only take rows older than the oldest still-open source transaction. Everything
            # below that point is final, so nothing read now can be joined later by a late row.
            src.execute("BEGIN")
            h = src.execute("SELECT v FROM horizon").fetchall()[0][0]
            rows = src.execute("SELECT event_id, ts, payload FROM events WHERE ts > ? AND ts < ? "
                               "ORDER BY event_id", (wm, h)).fetchall()
            src.execute("COMMIT")
            ctx.wm_override = max(wm, h - 1)
            ctx.rows_read += len(rows)
            return rows
        else:
            raise ValueError(ctx.predicate)
        rows = src.execute(q + " ORDER BY event_id", (arg,)).fetchall()
    finally:
        src.close()
    ctx.rows_read += len(rows)
    return rows


def new_wm(ctx: Ctx, wm: int, rows) -> int:
    if ctx.wm_override is not None:
        return ctx.wm_override
    return max([wm] + [r[1] for r in rows])


def set_wm(c, ctx: Ctx, old: int, new: int) -> None:
    """Write the watermark. 'cas' only succeeds if nobody moved it since we read it."""
    if ctx.guard == "none":
        c.execute("UPDATE state SET v=? WHERE k='wm'", (new,))
    elif ctx.guard == "monotonic":
        c.execute("UPDATE state SET v=MAX(v, ?) WHERE k='wm'", (new,))
    elif ctx.guard == "cas":
        cur = c.execute("UPDATE state SET v=? WHERE k='wm' AND v=?", (new, old))
        if cur.rowcount == 0:
            raise Fenced(f"watermark is no longer {old}")
    else:
        raise ValueError(ctx.guard)


def fsync_write(path: str, data: bytes, ctx: Ctx, partial_cp: str) -> None:
    """Write a file; if the harness targets ``partial_cp``, write half and die."""
    with open(path, "wb") as f:
        if ctx.crash_at == partial_cp:
            f.write(data[: len(data) // 2])
            f.flush()
            os.fsync(f.fileno())
            ctx.cp(partial_cp)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def fsync_dir(path: str) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Pattern:
    name = "base"
    family = ""
    description = ""
    crash_points: list[str] = []

    def setup(self, workdir: str) -> None: ...
    def run(self, ctx: Ctx) -> None: ...
    def read_view(self, workdir: str) -> list[int]:
        """Return event_ids as a downstream consumer would see them (dups included)."""
        raise NotImplementedError

    def storage_rows(self, workdir: str) -> int:
        """Physical rows stored, including anything the consumer view hides."""
        return len(self.read_view(workdir))


class SqlitePattern(Pattern):
    keyed = False

    def db(self, workdir: str) -> sqlite3.Connection:
        c = sqlite3.connect(os.path.join(workdir, "target.db"), isolation_level=None)
        c.execute("PRAGMA synchronous=FULL")
        return c

    def setup(self, workdir):
        c = self.db(workdir)
        pk = " PRIMARY KEY" if self.keyed else ""
        c.execute(f"CREATE TABLE IF NOT EXISTS t(event_id INTEGER{pk}, ts INTEGER, payload INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS state(k TEXT PRIMARY KEY, v INTEGER)")
        c.execute("INSERT OR IGNORE INTO state VALUES('wm', 0)")
        c.close()

    def get_wm(self, c) -> int:
        return c.execute("SELECT v FROM state WHERE k='wm'").fetchall()[0][0]

    def read_view(self, workdir):
        c = self.db(workdir)
        try:
            return [r[0] for r in c.execute("SELECT event_id FROM t")]
        finally:
            c.close()

    def _with_conn(self, ctx, body):
        c = self.db(ctx.workdir)
        try:
            body(c)
        finally:
            c.close()  # on Crash: open txn is discarded, i.e. rolled back


# Row-append family
class AppendThenWatermark(SqlitePattern):
    name, family = "A1", "append"
    description = "INSERT batch (txn 1), then advance watermark (txn 2)"
    crash_points = ["after_extract", "mid_data_txn", "after_data_commit", "after_wm_commit"]

    def run(self, ctx):
        def body(c):
            wm = self.get_wm(c)
            rows = extract(ctx, wm)
            ctx.cp("after_extract")
            c.execute("BEGIN")
            c.executemany("INSERT INTO t VALUES (?,?,?)", rows)
            ctx.cp("mid_data_txn")
            c.execute("COMMIT")
            ctx.cp("after_data_commit")
            c.execute("BEGIN")
            set_wm(c, ctx, wm, new_wm(ctx, wm, rows))
            c.execute("COMMIT")
            ctx.cp("after_wm_commit")
        self._with_conn(ctx, body)


class WatermarkThenAppend(SqlitePattern):
    name, family = "A2", "append"
    description = "Advance watermark (txn 1), then INSERT batch (txn 2)"
    crash_points = ["after_extract", "after_wm_commit", "mid_data_txn", "after_data_commit"]

    def run(self, ctx):
        def body(c):
            wm = self.get_wm(c)
            rows = extract(ctx, wm)
            ctx.cp("after_extract")
            c.execute("BEGIN")
            set_wm(c, ctx, wm, new_wm(ctx, wm, rows))
            c.execute("COMMIT")
            ctx.cp("after_wm_commit")
            c.execute("BEGIN")
            c.executemany("INSERT INTO t VALUES (?,?,?)", rows)
            ctx.cp("mid_data_txn")
            c.execute("COMMIT")
            ctx.cp("after_data_commit")
        self._with_conn(ctx, body)


class AppendDedupOnRead(AppendThenWatermark):
    name, family = "A3", "append"
    description = "As A1, but consumers read through a SELECT DISTINCT view"

    def read_view(self, workdir):
        c = self.db(workdir)
        try:
            return [r[0] for r in c.execute("SELECT DISTINCT event_id FROM t")]
        finally:
            c.close()

    def storage_rows(self, workdir):
        return len(SqlitePattern.read_view(self, workdir))


class AppendWatermarkAtomic(SqlitePattern):
    name, family = "A4", "append"
    description = "INSERT batch and advance watermark in one transaction"
    crash_points = ["after_extract", "mid_txn", "after_commit"]

    def run(self, ctx):
        def body(c):
            wm = self.get_wm(c)
            rows = extract(ctx, wm)
            ctx.cp("after_extract")
            c.execute("BEGIN")
            c.executemany("INSERT INTO t VALUES (?,?,?)", rows)
            set_wm(c, ctx, wm, new_wm(ctx, wm, rows))
            ctx.cp("mid_txn")
            c.execute("COMMIT")
            ctx.cp("after_commit")
        self._with_conn(ctx, body)


# Keyed merge family
UPSERT = ("INSERT INTO t VALUES (?,?,?) ON CONFLICT(event_id) "
          "DO UPDATE SET ts=excluded.ts, payload=excluded.payload")


class MergeThenWatermark(SqlitePattern):
    name, family, keyed = "M1", "merge", True
    description = "Upsert on key (txn 1), then advance watermark (txn 2)"
    crash_points = ["after_extract", "mid_data_txn", "after_data_commit", "after_wm_commit"]

    def run(self, ctx):
        def body(c):
            wm = self.get_wm(c)
            rows = extract(ctx, wm)
            ctx.cp("after_extract")
            c.execute("BEGIN")
            c.executemany(UPSERT, rows)
            ctx.cp("mid_data_txn")
            c.execute("COMMIT")
            ctx.cp("after_data_commit")
            c.execute("BEGIN")
            set_wm(c, ctx, wm, new_wm(ctx, wm, rows))
            c.execute("COMMIT")
            ctx.cp("after_wm_commit")
        self._with_conn(ctx, body)


class MergeWatermarkAtomic(SqlitePattern):
    name, family, keyed = "M2", "merge", True
    description = "Upsert on key and advance watermark in one transaction"
    crash_points = ["after_extract", "mid_txn", "after_commit"]

    def run(self, ctx):
        def body(c):
            wm = self.get_wm(c)
            rows = extract(ctx, wm)
            ctx.cp("after_extract")
            c.execute("BEGIN")
            c.executemany(UPSERT, rows)
            set_wm(c, ctx, wm, new_wm(ctx, wm, rows))
            ctx.cp("mid_txn")
            c.execute("COMMIT")
            ctx.cp("after_commit")
        self._with_conn(ctx, body)


# Partition overwrite family
def _partition_rows(ctx, parts):
    src = sqlite3.connect(ctx.source_path)
    try:
        out = []
        for p in sorted(parts):
            lo, hi = p * PARTITION_WIDTH, (p + 1) * PARTITION_WIDTH
            out += src.execute(
                "SELECT event_id, ts, payload FROM events WHERE ts >= ? AND ts < ?", (lo, hi)
            ).fetchall()
    finally:
        src.close()
    ctx.rows_read += len(out)
    return out


class PartitionOverwrite(SqlitePattern):
    name, family = "P1", "partition"
    description = "Recompute touched partitions: DELETE (txn 1), INSERT (txn 2), watermark (txn 3)"
    crash_points = ["after_extract", "after_delete_commit", "mid_insert_txn",
                    "after_insert_commit", "after_wm_commit"]

    def run(self, ctx):
        def body(c):
            wm = self.get_wm(c)
            rows = extract(ctx, wm)
            parts = {r[1] // PARTITION_WIDTH for r in rows}
            full = _partition_rows(ctx, parts)
            ctx.cp("after_extract")
            c.execute("BEGIN")
            for p in parts:
                c.execute("DELETE FROM t WHERE ts >= ? AND ts < ?",
                          (p * PARTITION_WIDTH, (p + 1) * PARTITION_WIDTH))
            c.execute("COMMIT")
            ctx.cp("after_delete_commit")
            c.execute("BEGIN")
            c.executemany("INSERT INTO t VALUES (?,?,?)", full)
            ctx.cp("mid_insert_txn")
            c.execute("COMMIT")
            ctx.cp("after_insert_commit")
            c.execute("BEGIN")
            set_wm(c, ctx, wm, new_wm(ctx, wm, rows))
            c.execute("COMMIT")
            ctx.cp("after_wm_commit")
        self._with_conn(ctx, body)


class PartitionOverwriteAtomic(SqlitePattern):
    name, family = "P2", "partition"
    description = "Recompute touched partitions: DELETE + INSERT + watermark in one transaction"
    crash_points = ["after_extract", "mid_txn", "after_commit"]

    def run(self, ctx):
        def body(c):
            wm = self.get_wm(c)
            rows = extract(ctx, wm)
            parts = {r[1] // PARTITION_WIDTH for r in rows}
            full = _partition_rows(ctx, parts)
            ctx.cp("after_extract")
            c.execute("BEGIN")
            for p in parts:
                c.execute("DELETE FROM t WHERE ts >= ? AND ts < ?",
                          (p * PARTITION_WIDTH, (p + 1) * PARTITION_WIDTH))
            c.executemany("INSERT INTO t VALUES (?,?,?)", full)
            set_wm(c, ctx, wm, new_wm(ctx, wm, rows))
            ctx.cp("mid_txn")
            c.execute("COMMIT")
            ctx.cp("after_commit")
        self._with_conn(ctx, body)


# File / lake family
def _lake(workdir):
    d = os.path.join(workdir, "lake")
    os.makedirs(os.path.join(d, "data"), exist_ok=True)
    return d


def _encode(rows) -> bytes:
    return "".join(json.dumps({"event_id": a, "ts": b, "payload": p}) + "\n"
                   for a, b, p in rows).encode()


def _decode(path) -> list[int]:
    out = []
    with open(path, "rb") as f:
        for line in f.read().decode(errors="replace").splitlines():
            try:
                out.append(json.loads(line)["event_id"])
            except (json.JSONDecodeError, KeyError) as e:
                raise Corrupt(f"{os.path.basename(path)}: {e}") from e
    return out


class FilesGlob(Pattern):
    name, family = "F1", "files"
    description = "Write part file, then watermark file; readers list the data directory"
    crash_points = ["after_extract", "mid_file_write", "after_file_write", "after_wm_write"]

    def setup(self, workdir):
        d = _lake(workdir)
        p = os.path.join(d, "wm.json")
        if not os.path.exists(p):
            with open(p, "w") as f:
                json.dump({"wm": 0}, f)

    def _wm(self, d):
        with open(os.path.join(d, "wm.json")) as f:
            return json.load(f)["wm"]

    def run(self, ctx):
        d = _lake(ctx.workdir)
        wm = self._wm(d)
        rows = extract(ctx, wm)
        ctx.cp("after_extract")
        if rows:
            fsync_write(os.path.join(d, "data", f"part-{uuid.uuid4().hex}.jsonl"),
                        _encode(rows), ctx, "mid_file_write")
            fsync_dir(os.path.join(d, "data"))
        ctx.cp("after_file_write")
        tmp = os.path.join(d, "wm.json.tmp")
        fsync_write(tmp, json.dumps({"wm": new_wm(ctx, wm, rows)}).encode(), ctx, "_never")
        os.replace(tmp, os.path.join(d, "wm.json"))
        fsync_dir(d)
        ctx.cp("after_wm_write")

    def read_view(self, workdir):
        out = []
        for p in sorted(glob.glob(os.path.join(_lake(workdir), "data", "*.jsonl"))):
            out += _decode(p)
        return out


class FilesManifestAtomic(Pattern):
    name, family = "F2", "files"
    description = "Write part file, then commit file list + watermark via atomic manifest rename"
    crash_points = ["after_extract", "mid_file_write", "after_file_write",
                    "after_manifest_tmp", "after_commit"]
    inplace = False

    def setup(self, workdir):
        d = _lake(workdir)
        p = os.path.join(d, "manifest.json")
        if not os.path.exists(p):
            with open(p, "w") as f:
                json.dump({"wm": 0, "files": []}, f)

    def _manifest(self, d):
        try:
            with open(os.path.join(d, "manifest.json")) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise Corrupt(f"manifest.json: {e}") from e

    def run(self, ctx):
        d = _lake(ctx.workdir)
        m = self._manifest(d)
        rows = extract(ctx, m["wm"])
        ctx.cp("after_extract")
        files = list(m["files"])
        if rows:
            name = f"part-{uuid.uuid4().hex}.jsonl"
            fsync_write(os.path.join(d, "data", name), _encode(rows), ctx, "mid_file_write")
            fsync_dir(os.path.join(d, "data"))
            files.append(name)
        ctx.cp("after_file_write")
        body = json.dumps({"wm": new_wm(ctx, m["wm"], rows), "files": files}).encode()
        if self.inplace:
            fsync_write(os.path.join(d, "manifest.json"), body, ctx, "mid_manifest_write")
        else:
            tmp = os.path.join(d, "manifest.json.tmp")
            fsync_write(tmp, body, ctx, "_never")
            ctx.cp("after_manifest_tmp")
            os.replace(tmp, os.path.join(d, "manifest.json"))
            fsync_dir(d)
        ctx.cp("after_commit")

    def read_view(self, workdir):
        d = _lake(workdir)
        out = []
        for name in self._manifest(d)["files"]:
            out += _decode(os.path.join(d, "data", name))
        return out

    def storage_rows(self, workdir):
        n = 0
        for p in glob.glob(os.path.join(_lake(workdir), "data", "*.jsonl")):
            with open(p, "rb") as f:
                n += f.read().count(b"\n")
        return n


class FilesManifestInPlace(FilesManifestAtomic):
    name, family = "F3", "files"
    description = "As F2, but the manifest is overwritten in place (open('w')) instead of renamed"
    crash_points = ["after_extract", "mid_file_write", "after_file_write",
                    "mid_manifest_write", "after_commit"]
    inplace = True


class MergeAdaptiveLookback(SqlitePattern):
    """M2 with a lookback window that grows when it catches late rows.

    The pipeline can only learn from late rows it actually finds. A row that is
    later than the current window is never seen, so it never teaches the window
    to grow. We wanted to know how much that costs.
    """
    name, family, keyed = "M2A", "merge", True
    description = "As M2, but the lookback window is learned from late rows it catches"
    crash_points = ["after_extract", "mid_txn", "after_commit"]
    start_window, growth = 5, 2.0

    def setup(self, workdir):
        super().setup(workdir)
        c = self.db(workdir)
        c.execute("INSERT OR IGNORE INTO state VALUES('L', ?)", (self.start_window,))
        c.close()

    def run(self, ctx):
        def body(c):
            wm = self.get_wm(c)
            L = c.execute("SELECT v FROM state WHERE k='L'").fetchall()[0][0]
            ctx.predicate, ctx.lookback = "lookback", L
            rows = extract(ctx, wm)
            have = set()
            ids = [r[0] for r in rows]
            for i in range(0, len(ids), 900):
                chunk = ids[i:i + 900]
                q = "SELECT event_id FROM t WHERE event_id IN (%s)" % ",".join("?" * len(chunk))
                have.update(x[0] for x in c.execute(q, chunk).fetchall())
            # how far back we had to reach for each row we had never seen before
            needed = [wm - r[1] + 1 for r in rows if r[0] not in have and r[1] <= wm]
            new_L = max([L] + [math.ceil(self.growth * n) for n in needed])
            ctx.cp("after_extract")
            c.execute("BEGIN")
            c.executemany(UPSERT, rows)
            set_wm(c, ctx, wm, new_wm(ctx, wm, rows))
            c.execute("UPDATE state SET v=? WHERE k='L'", (new_L,))
            ctx.cp("mid_txn")
            c.execute("COMMIT")
            ctx.cp("after_commit")
        self._with_conn(ctx, body)


class FilesVersionedLog(Pattern):
    """A tiny Delta-style log: each commit is a new numbered file, created only if absent.

    os.link() fails when the target exists, so two writers cannot both create
    version N. The loser gets Fenced instead of silently overwriting.
    """
    name, family = "F4", "files"
    description = "Write part file, then commit by creating log version N+1 only if it does not exist"
    crash_points = ["after_extract", "mid_file_write", "after_file_write", "after_log_tmp", "after_commit"]

    def _log(self, workdir):
        d = os.path.join(_lake(workdir), "_log")
        os.makedirs(d, exist_ok=True)
        return d

    def setup(self, workdir):
        p = os.path.join(self._log(workdir), "%08d.json" % 0)
        if not os.path.exists(p):
            with open(p, "w") as f:
                json.dump({"wm": 0, "files": []}, f)

    def _latest(self, workdir):
        d = self._log(workdir)
        names = sorted(n for n in os.listdir(d) if n.endswith(".json"))
        v = int(names[-1][:8])
        try:
            with open(os.path.join(d, names[-1])) as f:
                return v, json.load(f)
        except json.JSONDecodeError as e:
            raise Corrupt(f"{names[-1]}: {e}") from e

    def run(self, ctx):
        d = _lake(ctx.workdir)
        v, m = self._latest(ctx.workdir)
        rows = extract(ctx, m["wm"])
        ctx.cp("after_extract")
        files = list(m["files"])
        if rows:
            name = f"part-{uuid.uuid4().hex}.jsonl"
            fsync_write(os.path.join(d, "data", name), _encode(rows), ctx, "mid_file_write")
            fsync_dir(os.path.join(d, "data"))
            files.append(name)
        ctx.cp("after_file_write")
        log = self._log(ctx.workdir)
        tmp = os.path.join(log, f"tmp-{uuid.uuid4().hex}")
        fsync_write(tmp, json.dumps({"wm": new_wm(ctx, m["wm"], rows), "files": files}).encode(),
                    ctx, "_never")
        ctx.cp("after_log_tmp")
        try:
            os.link(tmp, os.path.join(log, "%08d.json" % (v + 1)))
        except FileExistsError:
            raise Fenced(f"log version {v + 1} already exists")
        finally:
            os.unlink(tmp)
        fsync_dir(log)
        ctx.cp("after_commit")

    def read_view(self, workdir):
        d = _lake(workdir)
        out = []
        for name in self._latest(workdir)[1]["files"]:
            out += _decode(os.path.join(d, "data", name))
        return out

    def storage_rows(self, workdir):
        return FilesManifestAtomic.storage_rows(self, workdir)


ALL = [AppendThenWatermark, WatermarkThenAppend, AppendDedupOnRead, AppendWatermarkAtomic,
       MergeThenWatermark, MergeWatermarkAtomic, PartitionOverwrite, PartitionOverwriteAtomic,
       FilesGlob, FilesManifestAtomic, FilesManifestInPlace]
EXTRA = [MergeAdaptiveLookback, FilesVersionedLog]
BY_NAME = {p.name: p for p in ALL + EXTRA}
