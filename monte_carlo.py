import numpy as np
import matplotlib.pyplot as plt
import os

np.random.seed(42)
N_SIMULATIONS = 10000
N_TRUCKS = 50

os.makedirs("results", exist_ok=True)

def simulate_one_truck(scenario="baseline"):
    total_time = 0

    arrival_rate = 12 if scenario != "s1_24hr" else 8
    servers      = 2  if scenario != "s1_24hr" else 4
    service_rate = 4
    rho = min(arrival_rate / (servers * service_rate), 0.98)
    total_time += np.random.exponential(1 / (service_rate * (1 - rho))) * 60

    doc_error_prob = 0.26 if scenario != "s3_docs" else 0.08
    total_time += np.random.triangular(10, 25, 60)
    if np.random.rand() < doc_error_prob:
        total_time += np.random.uniform(45, 120)

    ict_fail_prob    = 0.24 if scenario != "s2_ict" else 0.05
    ict_restore_mean = 45   if scenario != "s2_ict" else 10
    if np.random.rand() < ict_fail_prob:
        total_time += np.random.exponential(ict_restore_mean)
    total_time += np.random.triangular(10, 20, 40)

    scanner_ok = 0.86 if scenario != "s2_ict" else 0.97
    if np.random.rand() < scanner_ok:
        total_time += np.random.uniform(20, 50)
    else:
        total_time += np.random.uniform(60, 180)

    coord_prob = 0.36 if scenario != "s3_docs" else 0.20
    if np.random.rand() < coord_prob:
        total_time += np.random.triangular(20, 60, 120)

    return total_time

def simulate_combined():
    t = 0
    rho = min(8 / (4 * 4), 0.98)
    t += np.random.exponential(1 / (4 * (1 - rho))) * 60
    t += np.random.triangular(10, 25, 60)
    if np.random.rand() < 0.08:
        t += np.random.uniform(45, 120)
    if np.random.rand() < 0.05:
        t += np.random.exponential(10)
    t += np.random.triangular(10, 20, 40)
    if np.random.rand() < 0.97:
        t += np.random.uniform(20, 50)
    else:
        t += np.random.uniform(60, 180)
    if np.random.rand() < 0.20:
        t += np.random.triangular(20, 60, 120)
    return t

SCENARIOS = {
    "Baseline":          "baseline",
    "S1: 24-hr ops":     "s1_24hr",
    "S2: ICT upgrade":   "s2_ict",
    "S3: Pre-clearance": "s3_docs",
}

print("\n" + "="*60)
print("  MONTE CARLO — BOTSWANA BORDER CLEARANCE")
print("="*60)

results = {}
for label, key in SCENARIOS.items():
    daily = [np.mean([simulate_one_truck(key) for _ in range(N_TRUCKS)])
             for _ in range(N_SIMULATIONS)]
    results[label] = daily

results["S4: Combined"] = [
    np.mean([simulate_combined() for _ in range(N_TRUCKS)])
    for _ in range(N_SIMULATIONS)
]

print(f"\n{'Scenario':<22} {'Mean (hrs)':>10} {'P95 (hrs)':>10} {'vs Baseline':>12}")
print("-"*58)
base_mean = np.mean(results["Baseline"])
for label, data in results.items():
    m   = np.mean(data)
    p95 = np.percentile(data, 95)
    diff = f"{((m-base_mean)/base_mean)*100:+.1f}%" if label != "Baseline" else "—"
    print(f"{label:<22} {m/60:>10.2f} {p95/60:>10.2f} {diff:>12}")

COLORS = {
    "Baseline":"#888780","S1: 24-hr ops":"#1D9E75",
    "S2: ICT upgrade":"#534AB7","S3: Pre-clearance":"#D85A30","S4: Combined":"#185FA5"
}

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Monte Carlo — Botswana Border Clearance", fontsize=13, fontweight="bold")

for label, data in results.items():
    axes[0].hist([x/60 for x in data], bins=60, alpha=0.55,
                 color=COLORS[label], label=label, density=True)
axes[0].set_xlabel("Mean daily clearance time (hours)")
axes[0].set_ylabel("Probability density")
axes[0].set_title("Distribution of clearance time")
axes[0].legend(fontsize=8)
axes[0].grid(axis="y", alpha=0.3)

labels = list(results.keys())
means  = [np.mean(results[l])/60 for l in labels]
ci95   = [1.96*np.std(results[l])/np.sqrt(N_SIMULATIONS)/60 for l in labels]
bars   = axes[1].bar(range(len(labels)), means, yerr=ci95, capsize=5,
                     color=[COLORS[l] for l in labels], edgecolor="white")
axes[1].set_xticks(range(len(labels)))
axes[1].set_xticklabels(labels, rotation=15, ha="right", fontsize=9)
axes[1].set_ylabel("Hours")
axes[1].set_title("Mean clearance time ± 95% CI")
axes[1].grid(axis="y", alpha=0.3)
for bar, val in zip(bars, means):
    axes[1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                 f"{val:.2f}h", ha="center", fontsize=8)

plt.tight_layout()
plt.savefig("results/monte_carlo_results.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nSaved: results/monte_carlo_results.png")
print("Run des_model.py next.\n")