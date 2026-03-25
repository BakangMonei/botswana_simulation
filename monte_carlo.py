"""
Monte Carlo simulation — Botswana border clearance time distributions.
Use run_monte_carlo() from main or scripts; do not rely on import side effects.
"""
from __future__ import annotations

import os
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = "results"
COLORS = {
    "Baseline": "#888780",
    "S1: 24-hr ops": "#1D9E75",
    "S2: ICT upgrade": "#534AB7",
    "S3: Pre-clearance": "#D85A30",
    "S4: Combined": "#185FA5",
}
SCENARIOS = {
    "Baseline": "baseline",
    "S1: 24-hr ops": "s1_24hr",
    "S2: ICT upgrade": "s2_ict",
    "S3: Pre-clearance": "s3_docs",
}


def _u01(rng: np.random.RandomState | np.random.Generator) -> float:
    if isinstance(rng, np.random.RandomState):
        return float(rng.rand())
    return float(rng.random())


def simulate_one_truck(
    scenario: str = "baseline",
    rng: np.random.RandomState | np.random.Generator | None = None,
) -> float:
    """If rng is None, uses global `np.random` (legacy), matching the original script."""
    total_time = 0.0

    arrival_rate = 12 if scenario != "s1_24hr" else 8
    servers = 2 if scenario != "s1_24hr" else 4
    service_rate = 4
    rho = min(arrival_rate / (servers * service_rate), 0.98)
    if rng is None:
        total_time += float(np.random.exponential(1 / (service_rate * (1 - rho))) * 60)
    else:
        total_time += float(rng.exponential(1 / (service_rate * (1 - rho))) * 60)

    doc_error_prob = 0.26 if scenario != "s3_docs" else 0.08
    if rng is None:
        total_time += float(np.random.triangular(10, 25, 60))
        if np.random.rand() < doc_error_prob:
            total_time += float(np.random.uniform(45, 120))
        ict_fail_prob = 0.24 if scenario != "s2_ict" else 0.05
        ict_restore_mean = 45 if scenario != "s2_ict" else 10
        if np.random.rand() < ict_fail_prob:
            total_time += float(np.random.exponential(ict_restore_mean))
        total_time += float(np.random.triangular(10, 20, 40))
        scanner_ok = 0.86 if scenario != "s2_ict" else 0.97
        if np.random.rand() < scanner_ok:
            total_time += float(np.random.uniform(20, 50))
        else:
            total_time += float(np.random.uniform(60, 180))
        coord_prob = 0.36 if scenario != "s3_docs" else 0.20
        if np.random.rand() < coord_prob:
            total_time += float(np.random.triangular(20, 60, 120))
    else:
        total_time += float(rng.triangular(10, 25, 60))
        if _u01(rng) < doc_error_prob:
            total_time += float(rng.uniform(45, 120))
        ict_fail_prob = 0.24 if scenario != "s2_ict" else 0.05
        ict_restore_mean = 45 if scenario != "s2_ict" else 10
        if _u01(rng) < ict_fail_prob:
            total_time += float(rng.exponential(ict_restore_mean))
        total_time += float(rng.triangular(10, 20, 40))
        scanner_ok = 0.86 if scenario != "s2_ict" else 0.97
        if _u01(rng) < scanner_ok:
            total_time += float(rng.uniform(20, 50))
        else:
            total_time += float(rng.uniform(60, 180))
        coord_prob = 0.36 if scenario != "s3_docs" else 0.20
        if _u01(rng) < coord_prob:
            total_time += float(rng.triangular(20, 60, 120))

    return total_time


def simulate_combined(rng: np.random.RandomState | np.random.Generator | None = None) -> float:
    t = 0.0
    rho = min(8 / (4 * 4), 0.98)
    if rng is None:
        t += float(np.random.exponential(1 / (4 * (1 - rho))) * 60)
        t += float(np.random.triangular(10, 25, 60))
        if np.random.rand() < 0.08:
            t += float(np.random.uniform(45, 120))
        if np.random.rand() < 0.05:
            t += float(np.random.exponential(10))
        t += float(np.random.triangular(10, 20, 40))
        if np.random.rand() < 0.97:
            t += float(np.random.uniform(20, 50))
        else:
            t += float(np.random.uniform(60, 180))
        if np.random.rand() < 0.20:
            t += float(np.random.triangular(20, 60, 120))
    else:
        t += float(rng.exponential(1 / (4 * (1 - rho))) * 60)
        t += float(rng.triangular(10, 25, 60))
        if _u01(rng) < 0.08:
            t += float(rng.uniform(45, 120))
        if _u01(rng) < 0.05:
            t += float(rng.exponential(10))
        t += float(rng.triangular(10, 20, 40))
        if _u01(rng) < 0.97:
            t += float(rng.uniform(20, 50))
        else:
            t += float(rng.uniform(60, 180))
        if _u01(rng) < 0.20:
            t += float(rng.triangular(20, 60, 120))
    return t


def run_monte_carlo(
    n_simulations: int = 10_000,
    n_trucks: int = 50,
    seed: int = 42,
    results_dir: str = RESULTS_DIR,
    show_plot: bool = False,
    save: bool = True,
) -> dict[str, Any]:
    """
    Run Monte Carlo across all scenarios. Saves figure to results_dir when save=True.
    Returns dict with results series, summary table rows, and output path.
    """
    os.makedirs(results_dir, exist_ok=True)
    # Same RNG consumption order as the original script (legacy MT19937).
    rs = np.random.RandomState(seed)
    results: dict[str, list[float]] = {}

    for label, key in SCENARIOS.items():
        daily = [
            float(np.mean([simulate_one_truck(key, rng=rs) for _ in range(n_trucks)]))
            for _ in range(n_simulations)
        ]
        results[label] = daily

    results["S4: Combined"] = [
        float(np.mean([simulate_combined(rng=rs) for _ in range(n_trucks)]))
        for _ in range(n_simulations)
    ]

    base_mean = float(np.mean(results["Baseline"]))
    summary_rows: list[dict[str, Any]] = []
    for label, data in results.items():
        m = float(np.mean(data))
        p95 = float(np.percentile(data, 95))
        diff = "—" if label == "Baseline" else f"{((m - base_mean) / base_mean) * 100:+.1f}%"
        summary_rows.append(
            {
                "Scenario": label,
                "Mean (hrs)": round(m / 60, 2),
                "P95 (hrs)": round(p95 / 60, 2),
                "vs Baseline": diff,
            }
        )

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Monte Carlo — Botswana Border Clearance", fontsize=13, fontweight="bold")

    for label, data in results.items():
        axes[0].hist(
            [x / 60 for x in data],
            bins=60,
            alpha=0.55,
            color=COLORS[label],
            label=label,
            density=True,
        )
    axes[0].set_xlabel("Mean daily clearance time (hours)")
    axes[0].set_ylabel("Probability density")
    axes[0].set_title("Distribution of clearance time")
    axes[0].legend(fontsize=8)
    axes[0].grid(axis="y", alpha=0.3)

    labels = list(results.keys())
    means = [float(np.mean(results[l])) / 60 for l in labels]
    ci95 = [1.96 * float(np.std(results[l])) / np.sqrt(n_simulations) / 60 for l in labels]
    bars = axes[1].bar(
        range(len(labels)),
        means,
        yerr=ci95,
        capsize=5,
        color=[COLORS[l] for l in labels],
        edgecolor="white",
    )
    axes[1].set_xticks(range(len(labels)))
    axes[1].set_xticklabels(labels, rotation=15, ha="right", fontsize=9)
    axes[1].set_ylabel("Hours")
    axes[1].set_title("Mean clearance time ± 95% CI")
    axes[1].grid(axis="y", alpha=0.3)
    for bar, val in zip(bars, means):
        axes[1].text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.05,
            f"{val:.2f}h",
            ha="center",
            fontsize=8,
        )

    plt.tight_layout()
    out_path = os.path.join(results_dir, "monte_carlo_results.png")
    if save:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
    if show_plot:
        plt.show()
    else:
        plt.close(fig)

    return {
        "results": results,
        "summary": summary_rows,
        "figure_path": out_path if save else None,
        "figure": fig if show_plot else None,
        "baseline_mean_min": base_mean,
    }


def print_summary(summary: list[dict[str, Any]]) -> None:
    print(f"\n{'Scenario':<22} {'Mean (hrs)':>10} {'P95 (hrs)':>10} {'vs Baseline':>12}")
    print("-" * 58)
    for row in summary:
        print(
            f"{row['Scenario']:<22} {row['Mean (hrs)']:>10.2f} "
            f"{row['P95 (hrs)']:>10.2f} {row['vs Baseline']:>12}"
        )


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  MONTE CARLO — BOTSWANA BORDER CLEARANCE")
    print("=" * 60)
    out = run_monte_carlo(show_plot=True, save=True)
    print_summary(out["summary"])
    print(f"\nSaved: {out['figure_path']}")
    print("Tip: use `streamlit run main.py` for the interactive dashboard.\n")
