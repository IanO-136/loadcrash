"""Turn results/*.csv into the tables and figures used in the paper.

    python experiments/analyze.py
Writes results/summary_*.csv, results/summary.md and figures/*.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "results")
F = os.path.join(ROOT, "figures")
os.makedirs(F, exist_ok=True)

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "figure.dpi": 200, "savefig.bbox": "tight", "legend.frameon": False, "lines.linewidth": 2,
})

md = []


def table(df, title):
    md.append(f"\n## {title}\n")
    md.append(df.to_markdown(index=False) if hasattr(df, "to_markdown") else df.to_string(index=False))


def outcome(g):
    """Classify a group of trials of one (pattern, crash point)."""
    tags = []
    if g.lost.sum():
        tags.append("LOSS")
    if g.duplicates.sum():
        tags.append("DUP")
    if g.corrupt_final.any() or g.stuck.any():
        tags.append("CORRUPT")
    final = "+".join(tags) or "ok"
    t = []
    if g.exp_regression.sum():
        t.append("regress")
    if g.exp_corrupt.any():
        t.append("unreadable")
    if g.exp_duplicates.sum():
        t.append("dup")
    return pd.Series({
        "trials": len(g),
        "final": final,
        "transient": "+".join(t) or "ok",
        "mean_lost": round(g.lost.mean(), 1),
        "mean_dup": round(g.duplicates.mean(), 1),
        "mean_storage_overhead": round(g.storage_overhead.mean(), 1),
        "mean_exp_regression": round(g.exp_regression.mean(), 1),
    })


# E1
e1 = pd.read_csv(os.path.join(R, "e1_crash_points.csv"))
assert e1.crash_fired.all(), "some crash points never fired"
assert (e1.phantoms == 0).all()
s1 = (e1.groupby(["pattern", "crash_point"], sort=False)
        .apply(outcome, include_groups=False).reset_index())
s1.to_csv(os.path.join(R, "summary_e1.csv"), index=False)
table(s1, f"E1: crash-point outcomes ({len(e1)} trials, ordered source)")

per_pattern = (e1.groupby("pattern", sort=False)
                 .agg(trials=("final_ok", "size"), crash_points=("crash_point", "nunique"),
                      final_bad=("final_ok", lambda x: int((~x).sum())),
                      transient_bad=("transient_ok", lambda x: int((~x).sum())))
                 .reset_index())
per_pattern["unsafe_points_final"] = per_pattern.pattern.map(
    s1[s1.final != "ok"].groupby("pattern").size()).fillna(0).astype(int)
per_pattern["unsafe_points_transient"] = per_pattern.pattern.map(
    s1[s1.transient != "ok"].groupby("pattern").size()).fillna(0).astype(int)
per_pattern.to_csv(os.path.join(R, "summary_e1_pattern.csv"), index=False)
table(per_pattern, "E1: per-pattern")

# E2
e2 = pd.read_csv(os.path.join(R, "e2_watermark_lag.csv"))
e2["pred"] = e2.apply(lambda r: r.predicate if r.predicate != "lookback" else f"lookback L={r.lookback}", axis=1)
e2["loss_pct"] = 100 * e2.lost / e2.source_rows
e2["dup_pct"] = 100 * e2.duplicates / e2.source_rows
e2["read_amp"] = e2.rows_read / e2.source_rows
s2 = (e2.groupby(["pattern", "pred", "p_lag"], sort=False)
        .agg(loss_pct=("loss_pct", "mean"), loss_max=("loss_pct", "max"), dup_pct=("dup_pct", "mean"),
             read_amp=("read_amp", "mean"), runs_with_loss=("lost", lambda x: int((x > 0).sum())),
             n=("lost", "size"))
        .reset_index().round(3))
s2.to_csv(os.path.join(R, "summary_e2.csv"), index=False)
table(s2[s2.p_lag.isin([0.0, 0.05, 0.2])], "E2: predicate x lag (subset)")

# Fig 1: loss vs lag for the atomic merge pattern
fig, ax = plt.subplots(figsize=(5.2, 3.0))
m2 = s2[s2.pattern == "M2"]
order = ["gt", "gte", "lookback L=2", "lookback L=5", "lookback L=10", "lookback L=15"]
for i, pred in enumerate(order):
    d = m2[m2.pred == pred]
    ax.plot(100 * d.p_lag, d.loss_pct, marker="o", markersize=4, color=SERIES[i], label=pred)
ax.set_xlabel("Source transactions that commit late (%)")
ax.set_ylabel("Source rows lost (%)")
ax.set_title("Atomic merge (M2): rows lost vs. late commits", loc="left", fontsize=10, color=INK)
ax.legend(title="extraction predicate", fontsize=8, title_fontsize=8, ncol=2)
fig.savefig(os.path.join(F, "fig_loss_vs_lag.png"))
plt.close(fig)

# Fig 2: lookback window vs loss, and vs read amplification (two panels, one axis each)
d = e2[(e2.pattern == "M2") & (e2.p_lag == 0.1)]
d = d.assign(L=d.apply(lambda r: 0 if r.predicate == "gt" else (r.lookback if r.predicate == "lookback" else None), axis=1))
d = d.dropna(subset=["L"]).groupby("L").agg(loss_pct=("loss_pct", "mean"), read_amp=("read_amp", "mean")).reset_index()
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 2.6))
a1.plot(d.L, d.loss_pct, marker="o", markersize=4, color=SERIES[0])
a1.axvline(15, color=INK2, linewidth=0.8, linestyle="--")
a1.text(15.4, a1.get_ylim()[1] * 0.85, "max lag", color=INK2, fontsize=8)
a1.set_xlabel("Lookback window L (ticks)")
a1.set_ylabel("Rows lost (%)")
a1.set_title("Completeness", loc="left", fontsize=10, color=INK)
a2.plot(d.L, d.read_amp, marker="o", markersize=4, color=SERIES[1])
a2.set_xlabel("Lookback window L (ticks)")
a2.set_ylabel("Rows read / rows in source")
a2.set_title("Cost", loc="left", fontsize=10, color=INK)
fig.suptitle("M2, 10% late commits", x=0.01, ha="left", fontsize=9, color=INK2)
fig.tight_layout()
fig.savefig(os.path.join(F, "fig_lookback_tradeoff.png"))
plt.close(fig)
d.round(3).to_csv(os.path.join(R, "summary_e2_lookback.csv"), index=False)

# E3
e3 = pd.read_csv(os.path.join(R, "e3_crash_and_lag.csv"))
e3["config"] = e3.pattern + " / " + e3.predicate + e3.apply(lambda r: f" L={r.lookback}" if r.predicate == "lookback" else "", axis=1)
e3["crash_point"] = e3.crash_point.fillna("(no crash)")
s3 = (e3.groupby(["config", "crash_point"], sort=False)
        .agg(n=("lost", "size"), runs_lost=("lost", lambda x: int((x > 0).sum())),
             runs_dup=("duplicates", lambda x: int((x > 0).sum())),
             mean_lost=("lost", "mean"), mean_dup=("duplicates", "mean"))
        .reset_index().round(1))
s3.to_csv(os.path.join(R, "summary_e3.csv"), index=False)
s3c = (e3.groupby("config", sort=False)
         .agg(trials=("lost", "size"), trials_with_loss=("lost", lambda x: int((x > 0).sum())),
              trials_with_dup=("duplicates", lambda x: int((x > 0).sum())),
              trials_correct=("final_ok", "sum"))
         .reset_index())
s3c.to_csv(os.path.join(R, "summary_e3_config.csv"), index=False)
table(s3c, "E3: crashes + 5% late commits, per configuration")

# E4
e4 = pd.read_csv(os.path.join(R, "e4_sigkill.csv"))
k = e4[e4.killed]
s4 = (e4.groupby("pattern", sort=False)
        .agg(trials=("killed", "size"), killed=("killed", "sum"),
             final_bad=("final_ok", lambda x: int((~x).sum())),
             lost=("lost", lambda x: int((x > 0).sum())),
             dup=("duplicates", lambda x: int((x > 0).sum())),
             corrupt=("corrupt_final", "sum"), stuck=("stuck", "sum"),
             transient_regress=("exp_regression", lambda x: int((x > 0).sum())),
             transient_unreadable=("exp_corrupt", "sum"))
        .reset_index())
s4["p_final_bad_given_kill"] = (s4.final_bad / s4.killed).round(3)
s4.to_csv(os.path.join(R, "summary_e4.csv"), index=False)
table(s4, f"E4: SIGKILL fuzzing ({len(e4)} runs)")

# where did kills land, and did outcomes match E1's prediction for that crash point?
e1_pred = s1.set_index(["pattern", "crash_point"]).final
kk = k.copy()


def predicted(r):
    # a kill after the last reached point X but before the next one lands *between* X and next;
    # the outcome of "dying after X" is what E1 measured for crash point X
    key = (r.pattern, r.last_cp)
    return e1_pred.get(key, "ok" if r.last_cp == "<start>" else "?")


kk["e1_predicts_ok"] = kk.apply(predicted, axis=1) == "ok"
agree = kk[kk.last_cp != "<start>"]
md.append(f"\n## E4 vs E1\nKilled runs: {len(k)}. Runs where E1 predicts ok and the kill was ok, "
          f"or E1 predicts an anomaly and one occurred: "
          f"{int((agree.e1_predicts_ok == agree.final_ok).sum())}/{len(agree)}\n")
mismatch = agree[agree.e1_predicts_ok != agree.final_ok]
md.append(mismatch.groupby(["pattern", "last_cp", "final_ok"]).size().to_string() if len(mismatch) else "(no mismatches)")

fig, ax = plt.subplots(figsize=(5.2, 3.0))
order4 = list(s4.pattern)
vals = 100 * s4.p_final_bad_given_kill
bars = ax.bar(order4, vals, color=SERIES[0], width=0.6)
for b, v in zip(bars, vals):
    lab = "0" if v == 0 else (f"{v:.1f}%" if v < 5 else f"{v:.0f}%")
    ax.text(b.get_x() + b.get_width() / 2, v + 0.6, lab, ha="center", fontsize=8,
            color=INK if v else INK2)
ax.set_ylabel("Killed runs left incorrect (%)")
ax.set_title("Real SIGKILL at a random instant: permanent damage", loc="left", fontsize=10, color=INK)
fig.savefig(os.path.join(F, "fig_sigkill.png"))
plt.close(fig)

with open(os.path.join(R, "summary.md"), "w") as f:
    f.write("\n".join(md))
print("\n".join(md))
