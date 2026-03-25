import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
import os

os.makedirs("results", exist_ok=True)
np.random.seed(42)
N = 5000

BASE = dict(doc_error=0.26, ict_fail=0.24, coord_prob=0.36,
            scanner_ok=0.86, ict_restore=45, arrival_rate=12, servers=2)

def simulate_truck(doc_error, ict_fail, coord_prob, scanner_ok,
                   ict_restore, arrival_rate, servers):
    t = 0
    rho = min(arrival_rate / (servers * 4.0), 0.98)
    t += np.random.exponential(1 / (4.0 * (1 - rho))) * 60
    t += np.random.triangular(10, 25, 60)
    if np.random.rand() < doc_error:   t += np.random.uniform(45, 120)
    if np.random.rand() < ict_fail:    t += np.random.exponential(ict_restore)
    t += np.random.triangular(10, 20, 40)
    if np.random.rand() < scanner_ok:  t += np.random.uniform(20, 50)
    else:                              t += np.random.uniform(60, 180)
    if np.random.rand() < coord_prob:  t += np.random.triangular(20, 60, 120)
    return t

def run_mean(**overrides):
    p = {**BASE, **overrides}
    return np.mean([simulate_truck(**p) for _ in range(N)])

base_mean = run_mean()

params = {
    "Doc error prob":    ("doc_error",    0.08, 0.50),
    "ICT failure prob":  ("ict_fail",     0.05, 0.50),
    "Coord delay prob":  ("coord_prob",   0.10, 0.60),
    "Scanner avail":     ("scanner_ok",   0.70, 0.99),
    "ICT restore (min)": ("ict_restore",  10,   90),
    "Arrival rate":      ("arrival_rate", 8,    16),
    "Servers":           ("servers",      1,    4),
}

print("\n" + "="*60)
print("  SENSITIVITY ANALYSIS")
print("="*60)
print(f"\n{'Parameter':<22} {'CT @ low':>10} {'CT @ high':>10} {'Swing (min)':>12}")
print("-"*58)

tornado_rows = []
for label, (key, lo, hi) in params.items():
    ct_lo = run_mean(**{key: lo})
    ct_hi = run_mean(**{key: hi})
    swing = abs(ct_hi - ct_lo)
    tornado_rows.append((label, lo, hi, ct_lo, ct_hi, swing))
    print(f"{label:<22} {ct_lo:>10.1f} {ct_hi:>10.1f} {swing:>12.1f}")

tornado_rows.sort(key=lambda x: x[5], reverse=True)

mc_results = [simulate_truck(
    doc_error    = np.random.uniform(0.10, 0.45),
    ict_fail     = np.random.uniform(0.05, 0.45),
    coord_prob   = np.random.uniform(0.15, 0.55),
    scanner_ok   = np.random.uniform(0.70, 0.99),
    ict_restore  = np.random.uniform(15, 80),
    arrival_rate = np.random.uniform(8, 16),
    servers      = int(np.random.choice([1, 2, 3, 4])),
) for _ in range(N)]

print(f"\nFull uncertainty range:")
print(f"  Mean : {np.mean(mc_results)/60:.2f} hrs")
print(f"  P95  : {np.percentile(mc_results,95)/60:.2f} hrs")

fig = plt.figure(figsize=(15, 9))
fig.suptitle("Sensitivity Analysis — Botswana Border Clearance", fontsize=13, fontweight="bold")
gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

ax1 = fig.add_subplot(gs[0, :])
labels = [r[0] for r in tornado_rows]
base_h = base_mean / 60
for i, row in enumerate(tornado_rows):
    lo_h = row[3]/60; hi_h = row[4]/60
    ax1.barh(i, lo_h - base_h, left=base_h,
             color="#1D9E75" if lo_h < base_h else "#E24B4A", alpha=0.8, height=0.5)
    ax1.barh(i, hi_h - base_h, left=base_h,
             color="#E24B4A" if hi_h > base_h else "#1D9E75", alpha=0.8, height=0.5)
ax1.axvline(base_h, color="black", linewidth=1, linestyle="--", alpha=0.7)
ax1.set_yticks(range(len(labels))); ax1.set_yticklabels(labels, fontsize=9)
ax1.set_xlabel("Mean clearance time (hours)")
ax1.set_title("Tornado chart — which parameters matter most")
ax1.grid(axis="x", alpha=0.3)
ax1.legend(handles=[Patch(color="#1D9E75", label="Improvement"),
                    Patch(color="#E24B4A", label="Worsening")], fontsize=8)

ax2 = fig.add_subplot(gs[1, 0])
ax2.hist([x/60 for x in mc_results], bins=60, color="#378ADD", alpha=0.75, edgecolor="white")
ax2.axvline(np.percentile(mc_results,95)/60, color="#E24B4A", linestyle="--",
            linewidth=1.2, label=f"P95={np.percentile(mc_results,95)/60:.1f}h")
ax2.axvline(np.mean(mc_results)/60, color="#1D9E75", linestyle="--",
            linewidth=1.2, label=f"Mean={np.mean(mc_results)/60:.1f}h")
ax2.set_xlabel("Clearance time (hours)"); ax2.set_ylabel("Frequency")
ax2.set_title("Distribution under full parameter uncertainty")
ax2.legend(fontsize=8); ax2.grid(axis="y", alpha=0.3)

ax3 = fig.add_subplot(gs[1, 1])
swings = [r[5]/60 for r in tornado_rows]
colors = ["#185FA5","#534AB7","#1D9E75","#D85A30","#BA7517","#888780","#D4537E"]
bars = ax3.barh(range(len(labels)), swings,
                color=colors[:len(labels)], edgecolor="white", linewidth=0.5)
ax3.set_yticks(range(len(labels))); ax3.set_yticklabels(labels, fontsize=9)
ax3.set_xlabel("Swing in clearance time (hours)")
ax3.set_title("Total parameter impact (swing)")
ax3.grid(axis="x", alpha=0.3)
for b, v in zip(bars, swings):
    ax3.text(v+0.02, b.get_y()+b.get_height()/2, f"{v:.2f}h", va="center", fontsize=8)

plt.savefig("results/sensitivity_results.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nSaved: results/sensitivity_results.png")
print("\nAll done! Your results folder contains:")
print("  monte_carlo_results.png")
print("  des_results.png")
print("  sensitivity_results.png")
print("  kpi_summary.csv\n")