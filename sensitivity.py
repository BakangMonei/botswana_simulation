"""
Sensitivity analysis — tornado chart and uncertainty propagation.
Use run_sensitivity() from main or scripts.
"""
from __future__ import annotations

import os
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

RESULTS_DIR = "results"
DEFAULT_BASE = {
    "doc_error": 0.26,
    "ict_fail": 0.24,
    "coord_prob": 0.36,
    "scanner_ok": 0.86,
    "ict_restore": 45.0,
    "arrival_rate": 12.0,
    "servers": 2,
}
DEFAULT_PARAM_RANGES = {
    "Doc error prob": ("doc_error", 0.08, 0.50),
    "ICT failure prob": ("ict_fail", 0.05, 0.50),
    "Coord delay prob": ("coord_prob", 0.10, 0.60),
    "Scanner avail": ("scanner_ok", 0.70, 0.99),
    "ICT restore (min)": ("ict_restore", 10.0, 90.0),
    "Arrival rate": ("arrival_rate", 8.0, 16.0),
    "Servers": ("servers", 1, 4),
}


def simulate_truck(
    doc_error: float,
    ict_fail: float,
    coord_prob: float,
    scanner_ok: float,
    ict_restore: float,
    arrival_rate: float,
    servers: int,
    rng: np.random.Generator | None = None,
) -> float:
    g = rng if rng is not None else np.random.default_rng()
    t = 0.0
    rho = min(arrival_rate / (servers * 4.0), 0.98)
    t += g.exponential(1 / (4.0 * (1 - rho))) * 60
    t += g.triangular(10, 25, 60)
    if g.random() < doc_error:
        t += g.uniform(45, 120)
    if g.random() < ict_fail:
        t += g.exponential(ict_restore)
    t += g.triangular(10, 20, 40)
    if g.random() < scanner_ok:
        t += g.uniform(20, 50)
    else:
        t += g.uniform(60, 180)
    if g.random() < coord_prob:
        t += g.triangular(20, 60, 120)
    return t


def run_mean(
    n_samples: int,
    base: dict[str, Any],
    seed: int,
    **overrides: Any,
) -> float:
    p = {**base, **overrides}
    servers = int(p["servers"])
    g = np.random.default_rng(seed)
    return float(
        np.mean(
            [
                simulate_truck(
                    float(p["doc_error"]),
                    float(p["ict_fail"]),
                    float(p["coord_prob"]),
                    float(p["scanner_ok"]),
                    float(p["ict_restore"]),
                    float(p["arrival_rate"]),
                    servers,
                    rng=g,
                )
                for _ in range(n_samples)
            ]
        )
    )


def run_sensitivity(
    n_samples: int = 5000,
    seed: int = 42,
    base: dict[str, Any] | None = None,
    param_ranges: dict[str, tuple[str, float, float]] | None = None,
    results_dir: str = RESULTS_DIR,
    show_plot: bool = False,
    save: bool = True,
) -> dict[str, Any]:
    """
    Tornado chart + Monte Carlo over uncertain inputs. Saves sensitivity_results.png.
    """
    os.makedirs(results_dir, exist_ok=True)
    b = dict(DEFAULT_BASE if base is None else {**DEFAULT_BASE, **base})
    b["servers"] = int(b["servers"])
    pr = param_ranges if param_ranges is not None else DEFAULT_PARAM_RANGES

    base_mean = run_mean(n_samples, b, seed)

    tornado_rows: list[tuple[str, float, float, float, float, float]] = []
    for label, (key, lo, hi) in pr.items():
        ct_lo = run_mean(n_samples, b, seed + 1, **{key: lo})
        ct_hi = run_mean(n_samples, b, seed + 2, **{key: hi})
        swing = abs(ct_hi - ct_lo)
        tornado_rows.append((label, lo, hi, ct_lo, ct_hi, swing))

    tornado_rows.sort(key=lambda x: x[5], reverse=True)
    labels = [r[0] for r in tornado_rows]

    g_mc = np.random.default_rng(seed + 99)
    mc_results: list[float] = []
    for _ in range(n_samples):
        mc_results.append(
            simulate_truck(
                doc_error=float(g_mc.uniform(0.10, 0.45)),
                ict_fail=float(g_mc.uniform(0.05, 0.45)),
                coord_prob=float(g_mc.uniform(0.15, 0.55)),
                scanner_ok=float(g_mc.uniform(0.70, 0.99)),
                ict_restore=float(g_mc.uniform(15, 80)),
                arrival_rate=float(g_mc.uniform(8, 16)),
                servers=int(g_mc.choice([1, 2, 3, 4])),
                rng=g_mc,
            )
        )

    fig = plt.figure(figsize=(15, 9))
    fig.suptitle(
        "Sensitivity Analysis — Botswana Border Clearance",
        fontsize=13,
        fontweight="bold",
    )
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    ax1 = fig.add_subplot(gs[0, :])
    base_h = base_mean / 60
    for i, row in enumerate(tornado_rows):
        lo_h = row[3] / 60
        hi_h = row[4] / 60
        ax1.barh(
            i,
            lo_h - base_h,
            left=base_h,
            color="#1D9E75" if lo_h < base_h else "#E24B4A",
            alpha=0.8,
            height=0.5,
        )
        ax1.barh(
            i,
            hi_h - base_h,
            left=base_h,
            color="#E24B4A" if hi_h > base_h else "#1D9E75",
            alpha=0.8,
            height=0.5,
        )
    ax1.axvline(base_h, color="black", linewidth=1, linestyle="--", alpha=0.7)
    ax1.set_yticks(range(len(labels)))
    ax1.set_yticklabels(labels, fontsize=9)
    ax1.set_xlabel("Mean clearance time (hours)")
    ax1.set_title("Tornado chart — which parameters matter most")
    ax1.grid(axis="x", alpha=0.3)
    ax1.legend(
        handles=[
            Patch(color="#1D9E75", label="Improvement"),
            Patch(color="#E24B4A", label="Worsening"),
        ],
        fontsize=8,
    )

    ax2 = fig.add_subplot(gs[1, 0])
    ax2.hist([x / 60 for x in mc_results], bins=60, color="#378ADD", alpha=0.75, edgecolor="white")
    p95v = float(np.percentile(mc_results, 95))
    meanv = float(np.mean(mc_results))
    ax2.axvline(p95v / 60, color="#E24B4A", linestyle="--", linewidth=1.2, label=f"P95={p95v/60:.1f}h")
    ax2.axvline(meanv / 60, color="#1D9E75", linestyle="--", linewidth=1.2, label=f"Mean={meanv/60:.1f}h")
    ax2.set_xlabel("Clearance time (hours)")
    ax2.set_ylabel("Frequency")
    ax2.set_title("Distribution under full parameter uncertainty")
    ax2.legend(fontsize=8)
    ax2.grid(axis="y", alpha=0.3)

    ax3 = fig.add_subplot(gs[1, 1])
    swings = [r[5] / 60 for r in tornado_rows]
    bar_colors = ["#185FA5", "#534AB7", "#1D9E75", "#D85A30", "#BA7517", "#888780", "#D4537E"]
    bars = ax3.barh(
        range(len(labels)),
        swings,
        color=bar_colors[: len(labels)],
        edgecolor="white",
        linewidth=0.5,
    )
    ax3.set_yticks(range(len(labels)))
    ax3.set_yticklabels(labels, fontsize=9)
    ax3.set_xlabel("Swing in clearance time (hours)")
    ax3.set_title("Total parameter impact (swing)")
    ax3.grid(axis="x", alpha=0.3)
    for bbar, v in zip(bars, swings):
        ax3.text(v + 0.02, bbar.get_y() + bbar.get_height() / 2, f"{v:.2f}h", va="center", fontsize=8)

    fig.subplots_adjust(left=0.08, right=0.98, top=0.91, bottom=0.07, hspace=0.45, wspace=0.35)
    out_path = os.path.join(results_dir, "sensitivity_results.png")
    if save:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")

    if show_plot:
        plt.show()
    else:
        plt.close(fig)

    summary = {
        "baseline_mean_hrs": base_mean / 60,
        "mc_mean_hrs": meanv / 60,
        "mc_p95_hrs": p95v / 60,
        "tornado_table": [
            {
                "Parameter": row[0],
                "CT @ low (min)": round(row[3], 1),
                "CT @ high (min)": round(row[4], 1),
                "Swing (min)": round(row[5], 1),
            }
            for row in tornado_rows
        ],
    }

    return {
        "figure_path": out_path if save else None,
        "tornado_rows": tornado_rows,
        "mc_results": mc_results,
        "summary": summary,
        "figure": fig if show_plot else None,
    }


def print_sensitivity_report(out: dict[str, Any]) -> None:
    s = out["summary"]
    print(f"\n{'Parameter':<22} {'CT @ low':>10} {'CT @ high':>10} {'Swing (min)':>12}")
    print("-" * 58)
    for row in s["tornado_table"]:
        print(
            f"{row['Parameter']:<22} {row['CT @ low (min)']:>10.1f} "
            f"{row['CT @ high (min)']:>10.1f} {row['Swing (min)']:>12.1f}"
        )
    print("\nFull uncertainty range:")
    print(f"  Mean : {s['mc_mean_hrs']:.2f} hrs")
    print(f"  P95  : {s['mc_p95_hrs']:.2f} hrs")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  SENSITIVITY ANALYSIS")
    print("=" * 60)
    out = run_sensitivity(show_plot=True, save=True)
    print_sensitivity_report(out)
    print(f"\nSaved: {out['figure_path']}")
    print("Tip: use `streamlit run main.py` for the interactive dashboard.\n")
