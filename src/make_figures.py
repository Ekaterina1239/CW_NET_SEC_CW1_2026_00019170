import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = Path(__file__).resolve().parent.parent / "results"
FIG = RESULTS / "figures"
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]      # fixed order: series 1, 2, 3, 4
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def read(name):
    with open(RESULTS / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def style(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    ax.set_ylabel(ylabel, color=MUTED)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(MUTED)
    ax.tick_params(colors=MUTED)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def grouped_bars(ax, groups, series, value, log=True, labels=True):
    width = 0.8 / len(series)
    for j, s in enumerate(series):
        xs = [i + (j - (len(series) - 1) / 2) * width for i in range(len(groups))]
        ys = [value(g, s) for g in groups]
        bars = ax.bar(xs, ys, width * 0.92, color=COLORS[j], label=s)
        if labels:
            for b, y in zip(bars, ys):
                ax.annotate(f"{y:,.0f}" if y >= 10 else f"{y:.1f}", (b.get_x() + b.get_width() / 2, y),
                            ha="center", va="bottom", fontsize=7, color=MUTED, xytext=(0, 2),
                            textcoords="offset points")
    ax.set_xticks(range(len(groups)), groups)
    if log:
        ax.set_yscale("log")
    ax.legend(frameon=False, fontsize=8)


def fig_throughput():
    rows = [r for r in read("benchmark_summary.csv") if r["operation"] == "encrypt"]
    sizes = list(dict.fromkeys(r["data"] for r in rows))
    modes = list(dict.fromkeys(r["mode"] for r in rows))
    get = {(r["data"], r["mode"]): float(r["throughput_MBps"]) for r in rows}
    fig, ax = plt.subplots(figsize=(7.5, 3.8), dpi=200)
    grouped_bars(ax, sizes, modes, lambda g, s: get[(g, s)])
    ax.set_xticks(range(len(sizes)), [f"{s}\n({int(next(r['bytes'] for r in rows if r['data'] == s)):,} B)" for s in sizes])
    style(ax, "Encryption throughput by mode and data size (median of 100 runs)", "MB/s (log scale)")
    fig.tight_layout(); fig.savefig(FIG / "fig_throughput.png"); plt.close(fig)


def fig_reuse_share():
    rows = read("simulation.csv")
    scen = list(dict.fromkeys(r["scenario"] for r in rows))
    strat = list(dict.fromkeys(r["strategy"] for r in rows))
    total = 20 * 365 * 144
    get = {(r["strategy"], r["scenario"]): 100 * int(r["nonce_reuses_20y"]) / total for r in rows}
    fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=200)
    grouped_bars(ax, strat, scen, lambda g, s: get[(g, s)], log=False)
    ax.set_xticks(range(len(strat)), [s.replace(" (", "\n(") for s in strat], fontsize=8)
    ax.set_ylim(0, 110)
    style(ax, "Share of messages sent with an already-used nonce over 20 years", "% of messages")
    fig.tight_layout(); fig.savefig(FIG / "fig_nonce_reuse.png"); plt.close(fig)


def fig_flash_lifetime():
    rows = [r for r in read("simulation.csv") if r["flash_lifetime_years"] != "inf"]
    scen = list(dict.fromkeys(r["scenario"] for r in rows))
    strat = list(dict.fromkeys(r["strategy"] for r in rows))
    get = {(r["strategy"], r["scenario"]): float(r["flash_lifetime_years"]) for r in rows}
    fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=200)
    grouped_bars(ax, strat, scen, lambda g, s: get[(g, s)])
    ax.axhline(20, color=INK, linewidth=1, linestyle="--")
    ax.annotate("20-year service life", (-0.45, 20), ha="left", va="bottom", fontsize=8, color=INK,
                xytext=(0, 2), textcoords="offset points")
    style(ax, "Flash lifetime by strategy (10,000 write cycles, no wear-levelling)", "years (log scale)")
    fig.tight_layout(); fig.savefig(FIG / "fig_flash_lifetime.png"); plt.close(fig)


def fig_b_choice():
    rows = read("b_sweep.csv")
    fig, ax = plt.subplots(figsize=(7.5, 3.8), dpi=200)
    for j, scen in enumerate(dict.fromkeys(r["scenario"] for r in rows)):
        pts = [r for r in rows if r["scenario"] == scen]
        ax.plot([int(r["B"]) for r in pts], [float(r["flash_lifetime_years"]) for r in pts],
                color=COLORS[j], linewidth=2, marker="o", markersize=5, label=scen)
        bmin = int(pts[0]["formula_B_min"])
        ax.axvline(bmin, color=COLORS[j], linewidth=1, linestyle=":")
        ax.annotate(f"formula B = {bmin}", (bmin, 0.05 + 0.28 * j), xycoords=("data", "axes fraction"),
                    rotation=90, fontsize=7, color=MUTED, xytext=(3, 0), textcoords="offset points")
    ax.axhline(20, color=INK, linewidth=1, linestyle="--")
    ax.annotate("20-year target", (10, 20), va="bottom", fontsize=8, color=INK)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Reserve-ahead block size B (log scale)", color=MUTED)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    style(ax, "Choosing B: simulated flash lifetime vs block size", "years (log scale)")
    fig.tight_layout(); fig.savefig(FIG / "fig_b_choice.png"); plt.close(fig)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    fig_throughput(); fig_reuse_share(); fig_flash_lifetime(); fig_b_choice()
    print("figures saved to", FIG)


if __name__ == "__main__":
    main()