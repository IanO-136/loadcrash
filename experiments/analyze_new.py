"""Summaries for E5 and E5b (zombie runs), E6 (watermark strategies) and E7 (horizon + crashes).

    python experiments/analyze_new.py
"""
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "results")
out = []


def show(df, title):
    out.append(f"\n## {title}\n")
    out.append(df.to_markdown(index=False))


# E5
e5 = pd.read_csv(os.path.join(R, "e5_zombie.csv"))
e5 = e5[e5.zombie_fired]
e5["bad"] = ~e5.final_ok
g = (e5.groupby(["pattern", "guard"], sort=False)
       .agg(trials=("bad", "size"), fenced=("zombie_fenced", "sum"),
            zombie_errors=("zombie_error", lambda x: int((x.fillna("") != "").sum())),
            with_loss=("lost", lambda x: int((x > 0).sum())),
            with_dup=("duplicates", lambda x: int((x > 0).sum())),
            mean_lost=("lost", "mean"), mean_dup=("duplicates", "mean"),
            correct=("final_ok", "sum"))
       .reset_index().round(1))
g.to_csv(os.path.join(R, "summary_e5.csv"), index=False)
show(g, f"E5: zombie runs ({len(e5)} trials where the stall happened)")
sp = (e5.groupby(["pattern", "guard", "stall_point"], sort=False)
        .agg(n=("bad", "size"), bad=("bad", "sum"), fenced=("zombie_fenced", "sum"),
             mean_lost=("lost", "mean"), mean_dup=("duplicates", "mean"))
        .reset_index().round(1))
sp.to_csv(os.path.join(R, "summary_e5_points.csv"), index=False)
show(sp, "E5 by stall point")

# E5b
e5b = pd.read_csv(os.path.join(R, "e5b_zombie_horizon.csv"))
e5b = e5b[e5b.zombie_fired]
g5b = (e5b.groupby(["pattern", "guard"], sort=False)
         .agg(trials=("final_ok", "size"), correct=("final_ok", "sum"), fenced=("zombie_fenced", "sum"),
              with_loss=("lost", lambda x: int((x > 0).sum())),
              with_dup=("duplicates", lambda x: int((x > 0).sum())))
         .reset_index())
g5b.to_csv(os.path.join(R, "summary_e5b.csv"), index=False)
show(g5b, f"E5b: zombie runs with commit-horizon extraction ({len(e5b)} trials)")

# E6
e6 = pd.read_csv(os.path.join(R, "e6_strategies.csv"))
e6["strategy"] = e6.apply(
    lambda r: ("adaptive lookback" if r.pattern == "M2A" else
               f"lookback {r.lookback}" if r.predicate == "lookback" else
               f"horizon ({r.pattern})" if r.predicate == "horizon" else r.predicate), axis=1)
e6["loss_pct"] = 100 * e6.lost / e6.source_rows
e6["dup_pct"] = 100 * e6.duplicates / e6.source_rows
e6["read_amp"] = e6.rows_read_sched / e6.source_rows
s6 = (e6.groupby(["lag_dist", "p_lag", "strategy"], sort=False)
        .agg(loss_pct=("loss_pct", "mean"), runs_with_loss=("lost", lambda x: int((x > 0).sum())),
             dup_pct=("dup_pct", "mean"), read_amp=("read_amp", "mean"),
             lat_p50=("lat_p50", "mean"), lat_p99=("lat_p99", "mean"), lat_max=("lat_max", "max"),
             n=("lost", "size"))
        .reset_index().round(3))
s6.to_csv(os.path.join(R, "summary_e6.csv"), index=False)
show(s6, f"E6: watermark strategies ({len(e6)} trials)")

# E7
e7 = pd.read_csv(os.path.join(R, "e7_horizon_crash.csv"))
s7 = (e7.groupby("pattern", sort=False)
        .agg(trials=("final_ok", "size"), crash_fired=("crash_fired", "sum"),
             correct=("final_ok", "sum"), with_dup=("duplicates", lambda x: int((x > 0).sum())),
             with_loss=("lost", lambda x: int((x > 0).sum())), corrupt=("corrupt_final", "sum"),
             transient_bad=("transient_ok", lambda x: int((~x).sum())))
        .reset_index())
s7.to_csv(os.path.join(R, "summary_e7.csv"), index=False)
show(s7, f"E7: horizon extraction with crashes ({len(e7)} trials, Pareto lag, 10% late)")
s7p = (e7.groupby(["pattern", "crash_point"], sort=False)
         .agg(n=("final_ok", "size"), correct=("final_ok", "sum"),
              mean_dup=("duplicates", "mean"), corrupt=("corrupt_final", "sum"))
         .reset_index().round(1))
show(s7p, "E7 by crash point")

with open(os.path.join(R, "summary_new.md"), "w") as f:
    f.write("\n".join(out))
print("\n".join(out))

# Figure 3: freshness cost of commit-horizon extraction (p99 delay by lag distribution and rate)
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

F = os.path.join(ROOT, "figures")
os.makedirs(F, exist_ok=True)
h = s6[s6.strategy == "horizon (M2)"]
dists = ["uniform", "lognormal", "pareto"]
fig, ax = plt.subplots(figsize=(6.4, 3.2))
w = 0.36
for i, (rate, color) in enumerate([(0.02, "#9cc3f0"), (0.1, "#2a78d6")]):
    ys = [float(h[(h.lag_dist == d) & (h.p_lag == rate)].lat_p99.iloc[0]) for d in dists]
    xs = [k + (i - 0.5) * w for k in range(len(dists))]
    bars = ax.bar(xs, ys, w * 0.92, color=color, label=f"{int(rate * 100)}% late")
    ax.bar_label(bars, fmt="%g", fontsize=8, padding=2)
other = float(s6[~s6.strategy.str.startswith("horizon")].lat_p99.max())
ax.axhline(other, color="#52514e", linestyle="--", linewidth=1, label=f"gt and lookback: {other:g} ticks")
ax.set_xticks(range(len(dists)), [f"{d.capitalize()} lag" for d in dists])
ax.set_ylabel("p99 freshness delay (ticks)")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, fontsize=8, loc="upper left")
fig.savefig(os.path.join(F, "fig_horizon_freshness.png"), dpi=200, bbox_inches="tight")
print("wrote figures/fig_horizon_freshness.png")
