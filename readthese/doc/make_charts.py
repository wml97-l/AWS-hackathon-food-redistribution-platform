"""
Build the README insight charts from agents/distribution_data.csv.

    python docs/make_charts.py

Writes light and dark PNGs to docs/charts/ and prints the headline figures.
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

COLS = ['line_id', 'category', 'subcategory', 'product_name', 'location', 'units_in',
        'initial_stock_kg', 'units_distributed', 'kg_distributed', 'final_stock_kg',
        'delta_units', 'delta_qty', 'unit_weight', 'value1', 'value2', 'bestbeforedate',
        'flag1', 'days_to_expiry', 'source_name', 'extra1', 'source_type',
        'created_date', 'updated_date']


def load():
    rows = []
    with open(ROOT / "agents" / "distribution_data.csv") as f:
        for r in csv.reader(f):
            n = len(r)
            if n < 23:
                continue
            k = n - 22  # product names containing unquoted commas
            rows.append(r[:3] + [",".join(r[3:3 + k])] + r[3 + k:])
    d = pd.DataFrame(rows, columns=COLS)
    for c in ["initial_stock_kg", "kg_distributed", "final_stock_kg"]:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    d["created_date"] = pd.to_datetime(d["created_date"], errors="coerce")
    d["source_type"] = d["source_type"].str.strip()
    d = d[d["location"].isin(["DUBLIN", "CORK", "GALWAY"])]  # drops ~1% malformed rows
    d["gap"] = d["initial_stock_kg"] - d["kg_distributed"]
    return d


THEMES = {
    "light": dict(bg="#ffffff", ink="#1f2328", ink2="#59636e", grid="#d8dee4",
                  main="#2a78d6", accent="#eb6834", muted="#b7c0ca"),
    "dark": dict(bg="#0d1117", ink="#f0f6fc", ink2="#9198a1", grid="#30363d",
                 main="#3987e5", accent="#d95926", muted="#4a535e"),
}


def style(ax, t, grid_axis="x"):
    ax.set_facecolor(t["bg"])
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(t["grid"])
    ax.tick_params(colors=t["ink2"], length=0, labelsize=10.5)
    ax.grid(axis=grid_axis, color=t["grid"], linewidth=0.8)
    ax.set_axisbelow(True)


def title(fig, t, head, sub):
    fig.text(0.02, 0.965, head, fontsize=15, fontweight="bold", color=t["ink"], va="top")
    fig.text(0.02, 0.885, sub, fontsize=11, color=t["ink2"], va="top")


def kfmt(v):
    return f"{v/1e6:.2f}M kg" if v >= 1e6 else f"{v/1e3:,.0f}k kg"


def save(fig, name, mode):
    fig.savefig(OUT / f"{name}-{mode}.png", dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)


def chart_gap(d, t, mode):
    """Where the undistributed food sits."""
    veg = d[d.category == "VEGETABLES"]
    pot = veg[veg.subcategory.str.startswith("POTATOES")].gap.sum()
    oveg = veg.gap.sum() - pot
    other = d[d.category != "VEGETABLES"].groupby("category").gap.sum().sort_values(ascending=False)
    top = other.head(5)
    rest = other.iloc[5:].sum()
    mids = sorted([("Other vegetables", oveg)] + [(c.title().replace("Smd", "SMD"), v) for c, v in top.items()],
                  key=lambda kv: -kv[1])
    labels = ["Potatoes"] + [k for k, _ in mids] + ["All other categories"]
    vals = [pot] + [v for _, v in mids] + [rest]
    colors = [t["accent"]] + [t["muted"]] * (len(vals) - 1)

    fig, ax = plt.subplots(figsize=(10, 4.6), facecolor=t["bg"])
    fig.subplots_adjust(left=0.2, right=0.9, top=0.78, bottom=0.08)
    y = range(len(vals))[::-1]
    ax.barh(list(y), vals, color=colors, height=0.62)
    ax.set_yticks(list(y), labels, color=t["ink"], fontsize=11)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1e3:,.0f}k"))
    total = d.gap.sum()
    for yi, v in zip(y, vals):
        ax.text(v + total * 0.008, yi, f"{kfmt(v)}  ({v/total:.0%})", va="center", fontsize=10.5,
                color=t["ink"] if v == pot else t["ink2"], fontweight="bold" if v == pot else "normal")
    ax.set_xlim(0, max(vals) * 1.32)
    style(ax, t)
    title(fig, t, f"Potatoes alone account for {pot/total:.0%} of all food left undistributed",
          f"Food received but not distributed, Jan to Oct 2024 (total {kfmt(total)})")
    save(fig, "undistributed-by-category", mode)
    return pot, total


def chart_pareto(d, t, mode):
    """How concentrated the problem is across 2,000+ products."""
    p = d.groupby("product_name").gap.sum()
    p = p[p > 0].sort_values(ascending=False)
    cum = (p.cumsum() / p.sum()).values
    n = len(cum)
    n50 = int((cum < 0.5).sum()) + 1
    n80 = int((cum < 0.8).sum()) + 1

    fig, ax = plt.subplots(figsize=(10, 4.4), facecolor=t["bg"])
    fig.subplots_adjust(left=0.08, right=0.97, top=0.78, bottom=0.14)
    x = range(1, n + 1)
    ax.plot(list(x), cum * 100, color=t["main"], linewidth=2)
    ax.set_xscale("log")
    for k in [n50, n80]:
        yv = cum[k - 1] * 100
        lab = f"{yv:.0f}%"
        ax.plot([k], [yv], "o", ms=8, color=t["accent"], mec=t["bg"], mew=2, zorder=5)
        ax.annotate(f"{k} products hold {lab} of the gap", (k, yv), xytext=(14, -18),
                    textcoords="offset points", fontsize=10.5, color=t["ink"], fontweight="bold")
    ax.set_ylim(0, 105)
    ax.set_xlim(0.9, n * 1.1)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.set_xlabel(f"Products ranked by kg left undistributed (log scale, {n:,} products)", color=t["ink2"], fontsize=10.5)
    style(ax, t, grid_axis="y")
    title(fig, t, f"Just {n50} of {n:,} products hold over half of all undistributed food",
          "Cumulative share of undistributed kg, by product")
    save(fig, "pareto-products", mode)
    return n50, n80, n


def chart_rates(d, t, mode):
    """Distribution rate by source type and by depot, side by side (same 0 to 100% scale)."""
    src = d[d.source_type.isin(["Surplus", "Growers", "ESF", "Donated"])].groupby("source_type")[
        ["initial_stock_kg", "kg_distributed"]].sum()
    src["rate"] = src.kg_distributed / src.initial_stock_kg
    src = src.sort_values("rate")
    loc = d.groupby("location")[["initial_stock_kg", "kg_distributed"]].sum()
    loc["rate"] = loc.kg_distributed / loc.initial_stock_kg
    loc = loc.sort_values("rate")
    overall = d.kg_distributed.sum() / d.initial_stock_kg.sum()

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), facecolor=t["bg"])
    fig.subplots_adjust(left=0.1, right=0.97, top=0.72, bottom=0.1, wspace=0.55)
    names = {"Surplus": "Retail surplus"}
    for ax, df, head, worst in [(axes[0], src, "By source", "Growers"), (axes[1], loc, "By depot", "CORK")]:
        labels = [names.get(i, i if i == "ESF" else i.title()) for i in df.index]
        cols = [t["accent"] if i == worst else t["main"] for i in df.index]
        ax.barh(labels, df.rate * 100, color=cols, height=0.58)
        for i, (r, kin) in enumerate(zip(df.rate, df.initial_stock_kg)):
            box = dict(facecolor=t["bg"], edgecolor="none", pad=1.5)
            ax.annotate(f"{r:.0%}", (r * 100, i), xytext=(6, 0), textcoords="offset points", va="center",
                        fontsize=10.5, color=t["ink"], fontweight="bold", bbox=box, zorder=4)
            ax.annotate(f"of {kfmt(kin)}", (r * 100, i), xytext=(38, 0), textcoords="offset points", va="center",
                        fontsize=9.5, color=t["ink2"], bbox=box, zorder=4)
        ax.axvline(overall * 100, color=t["ink2"], linestyle=(0, (3, 3)), linewidth=1)
        ax.set_xlim(0, 135)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
        ax.tick_params(axis="y", colors=t["ink"], labelsize=11)
        ax.set_title(head, loc="left", color=t["ink"], fontsize=12, fontweight="bold", pad=8)
        style(ax, t)
    fig.text(0.02, 0.965, "Grower donations and the Cork depot have the most room to improve",
             fontsize=15, fontweight="bold", color=t["ink"], va="top")
    fig.text(0.02, 0.885, f"Share of received kg that reached charities (dashed line = network average {overall:.0%})",
             fontsize=11, color=t["ink2"], va="top")
    save(fig, "rate-by-source-and-depot", mode)
    return src, loc, overall


def chart_monthly(d, t, mode):
    m = d[(d.created_date >= "2024-01-01") & (d.created_date < "2024-08-01")]
    g = m.groupby(m.created_date.dt.to_period("M"))[["initial_stock_kg", "kg_distributed"]].sum()
    labels = [p.strftime("%b") for p in g.index]

    fig, ax = plt.subplots(figsize=(10, 4.2), facecolor=t["bg"])
    fig.subplots_adjust(left=0.08, right=0.86, top=0.78, bottom=0.1)
    x = list(range(len(g)))
    ax.fill_between(x, g.kg_distributed, g.initial_stock_kg, color=t["accent"], alpha=0.18, linewidth=0)
    ax.plot(x, g.initial_stock_kg, color=t["ink2"], linewidth=2)
    ax.plot(x, g.kg_distributed, color=t["main"], linewidth=2)
    ax.plot(x, g.initial_stock_kg, "o", ms=6, color=t["ink2"], mec=t["bg"], mew=2)
    ax.plot(x, g.kg_distributed, "o", ms=6, color=t["main"], mec=t["bg"], mew=2)
    ax.text(x[-1] + 0.15, g.initial_stock_kg.iloc[-1], "Received", color=t["ink2"], va="center", fontsize=11, fontweight="bold")
    ax.text(x[-1] + 0.15, g.kg_distributed.iloc[-1], "Distributed", color=t["main"], va="center", fontsize=11, fontweight="bold")
    ax.text(1.5, (g.initial_stock_kg.iloc[1:3].mean() + g.kg_distributed.iloc[1:3].mean()) / 2, "not distributed",
            color=t["accent"], fontsize=10.5, fontweight="bold", va="center", ha="center")
    ax.set_xticks(x, labels)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1e3:,.0f}k"))
    ax.set_ylim(0, g.initial_stock_kg.max() * 1.1)
    ax.set_xlim(-0.3, x[-1] + 0.3)
    style(ax, t, grid_axis="y")
    title(fig, t, "Roughly a quarter of incoming food is left behind every month",
          "Kg received vs kg distributed per month, Jan to Jul 2024 (later months are partial in the extract)")
    save(fig, "monthly-received-vs-distributed", mode)
    return g


if __name__ == "__main__":
    d = load()
    for mode, t in THEMES.items():
        pot, total = chart_gap(d, t, mode)
        n50, n80, n = chart_pareto(d, t, mode)
        src, loc, overall = chart_rates(d, t, mode)
        g = chart_monthly(d, t, mode)

    veg = d[d.category == "VEGETABLES"]
    nonveg = d[d.category != "VEGETABLES"]
    nonveg_rate = nonveg.kg_distributed.sum() / nonveg.initial_stock_kg.sum()
    veg_rate = veg.kg_distributed.sum() / veg.initial_stock_kg.sum()
    uplift = nonveg_rate * veg.initial_stock_kg.sum() - veg.kg_distributed.sum()
    cork_uplift = loc.loc["GALWAY", "rate"] * loc.loc["CORK", "initial_stock_kg"] - loc.loc["CORK", "kg_distributed"]
    print(f"rows {len(d):,}  received {kfmt(d.initial_stock_kg.sum())}  distributed {kfmt(d.kg_distributed.sum())}  rate {overall:.1%}  gap {kfmt(total)}")
    print(f"veg share of intake {veg.initial_stock_kg.sum()/d.initial_stock_kg.sum():.1%}, of gap {veg.gap.sum()/total:.1%}, rate {veg_rate:.1%} vs others {nonveg_rate:.1%}")
    print(f"potatoes gap {kfmt(pot)} = {pot/total:.1%}; pareto n50 {n50}, n80 {n80} of {n}")
    print(f"uplift if veg matched others: {kfmt(uplift)} ({uplift/d.kg_distributed.sum():.1%} more food distributed)")
    print(f"uplift if Cork matched Galway: {kfmt(cork_uplift)}")
    print(src, loc, sep="\n")
