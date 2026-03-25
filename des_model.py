import simpy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import os

os.makedirs("results", exist_ok=True)
RANDOM_SEED = 42
SIM_HOURS   = 16
SIM_TIME    = SIM_HOURS * 60
N_REPLICATIONS = 30

SCENARIOS = {
    "Baseline":         dict(servers=2, ict_fail=0.24, ict_restore=45,
                             doc_error=0.26, coord_prob=0.36,
                             scanner_ok=0.86, arrival_rate=12),
    "S1: 24-hr ops":    dict(servers=4, ict_fail=0.24, ict_restore=45,
                             doc_error=0.26, coord_prob=0.36,
                             scanner_ok=0.86, arrival_rate=8),
    "S2: ICT upgrade":  dict(servers=2, ict_fail=0.05, ict_restore=10,
                             doc_error=0.26, coord_prob=0.36,
                             scanner_ok=0.97, arrival_rate=12),
    "S3: Pre-clearance":dict(servers=2, ict_fail=0.24, ict_restore=45,
                             doc_error=0.08, coord_prob=0.20,
                             scanner_ok=0.86, arrival_rate=12),
    "S4: Combined":     dict(servers=4, ict_fail=0.05, ict_restore=10,
                             doc_error=0.08, coord_prob=0.20,
                             scanner_ok=0.97, arrival_rate=8),
}

def run_one_replication(cfg, seed):
    rng = np.random.RandomState(seed)
    env = simpy.Environment()
    customs = simpy.Resource(env, capacity=cfg["servers"])
    scanner = simpy.Resource(env, capacity=1)
    clearance_times = []
    queue_snapshots = []
    busy_time = [0.0]

    def truck(tid):
        arrival = env.now
        with customs.request() as req:
            yield req
            t0 = env.now
            yield env.timeout(rng.triangular(10, 25, 60))
            if rng.rand() < cfg["doc_error"]:
                yield env.timeout(rng.uniform(45, 120))
            busy_time[0] += env.now - t0
        if rng.rand() < cfg["ict_fail"]:
            yield env.timeout(rng.exponential(cfg["ict_restore"]))
        yield env.timeout(rng.triangular(10, 20, 40))
        with scanner.request() as req:
            yield req
            if rng.rand() < cfg["scanner_ok"]:
                yield env.timeout(rng.uniform(20, 50))
            else:
                yield env.timeout(rng.uniform(60, 180))
        if rng.rand() < cfg["coord_prob"]:
            yield env.timeout(rng.triangular(20, 60, 120))
        clearance_times.append(env.now - arrival)

    def arrivals():
        tid = 0
        while True:
            yield env.timeout(rng.exponential(60 / cfg["arrival_rate"]))
            tid += 1
            env.process(truck(tid))

    def monitor():
        while True:
            queue_snapshots.append(len(customs.queue))
            yield env.timeout(1)

    env.process(arrivals())
    env.process(monitor())
    env.run(until=SIM_TIME)

    if not clearance_times:
        return None
    n       = len(clearance_times)
    mean_ct = np.mean(clearance_times)
    util    = busy_time[0] / (cfg["servers"] * SIM_TIME) * 100
    return {
        "n_trucks":    n,
        "mean_ct":     mean_ct,
        "p95_ct":      np.percentile(clearance_times, 95),
        "mean_queue":  np.mean(queue_snapshots),
        "utilisation": util,
        "L_littles":   (n / SIM_TIME) * mean_ct,
        "L_queue_obs": np.mean(queue_snapshots),
        "lambda_hr":   (n / SIM_TIME) * 60,
    }

print("\n" + "="*72)
print("  DISCRETE EVENT SIMULATION — BOTSWANA BORDER CLEARANCE")
print("="*72)

all_results = {}
for name, cfg in SCENARIOS.items():
    reps = [r for i in range(N_REPLICATIONS)
            if (r := run_one_replication(cfg, seed=i*7+13)) is not None]
    all_results[name] = reps

def stat(reps, key):
    v = [r[key] for r in reps]
    return np.mean(v), 1.96*np.std(v)/np.sqrt(len(v))

print(f"\n{'Scenario':<22} {'Mean CT':>13} {'P95 (hr)':>10} "
      f"{'Util%':>7} {'Queue':>7} {'Trucks':>7}")
print("-"*72)
base_ct = stat(all_results["Baseline"], "mean_ct")[0]
for name, reps in all_results.items():
    m, ci = stat(reps, "mean_ct")
    p95,_ = stat(reps, "p95_ct")
    u,  _ = stat(reps, "utilisation")
    q,  _ = stat(reps, "mean_queue")
    n,  _ = stat(reps, "n_trucks")
    pct   = f"({(m-base_ct)/base_ct*100:+.1f}%)" if name != "Baseline" else ""
    print(f"{name:<22} {m/60:>6.2f}±{ci/60:.2f} {pct:<8} "
          f"{p95/60:>8.2f} {u:>7.1f} {q:>7.2f} {n:>7.0f}")

print(f"\n── Little's Law Validation ──────────────────────────────────────")
print(f"{'Scenario':<22} {'λ(tr/hr)':>9} {'W(min)':>8} "
      f"{'L=λW':>8} {'L_queue':>9} {'Check':>8}")
print("-"*68)
for name, reps in all_results.items():
    lam = np.mean([r["lambda_hr"]  for r in reps])
    W   = np.mean([r["mean_ct"]    for r in reps])
    Ls  = np.mean([r["L_littles"]  for r in reps])
    Lq  = np.mean([r["L_queue_obs"] for r in reps])
    ok  = "PASS" if Ls > Lq else "CHECK"
    print(f"{name:<22} {lam:>9.2f} {W:>8.1f} {Ls:>8.2f} {Lq:>9.2f} {ok:>8}")

COLORS = {"Baseline":"#888780","S1: 24-hr ops":"#1D9E75",
          "S2: ICT upgrade":"#534AB7","S3: Pre-clearance":"#D85A30","S4: Combined":"#185FA5"}
names  = list(all_results.keys())
colors = [COLORS[n] for n in names]

fig = plt.figure(figsize=(16, 10))
fig.suptitle("DES Results — Botswana Border Clearance (30 replications)",
             fontsize=13, fontweight="bold")
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.5, wspace=0.35)

def bar_chart(ax, key, ylabel, title, div=1, fmt=".2f"):
    ms  = [stat(all_results[n], key)[0]/div for n in names]
    cis = [stat(all_results[n], key)[1]/div for n in names]
    bars = ax.bar(range(len(names)), ms, yerr=cis, capsize=4,
                  color=colors, edgecolor="white", linewidth=0.5)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=22, ha="right", fontsize=7)
    ax.set_ylabel(ylabel, fontsize=8); ax.set_title(title, fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    for b, v in zip(bars, ms):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+max(ms)*0.01,
                format(v, fmt), ha="center", fontsize=7)

bar_chart(fig.add_subplot(gs[0,0]), "mean_ct",    "Hours",  "Mean clearance time",    div=60)
bar_chart(fig.add_subplot(gs[0,1]), "utilisation","Util %", "Server utilisation")
bar_chart(fig.add_subplot(gs[0,2]), "mean_queue", "Trucks", "Mean queue length",      fmt=".1f")
bar_chart(fig.add_subplot(gs[1,0]), "p95_ct",     "Hours",  "P95 clearance time",     div=60)
bar_chart(fig.add_subplot(gs[1,2]), "n_trucks",   "Trucks", "Throughput (trucks/run)",fmt=".0f")

ax5 = fig.add_subplot(gs[1,1])
base = stat(all_results["Baseline"], "mean_ct")[0]
impr = [0]+[(base-stat(all_results[n],"mean_ct")[0])/base*100 for n in names[1:]]
ax5.bar(range(len(names)), impr,
        color=["#888780"]+["#1D9E75" if v>=0 else "#E24B4A" for v in impr[1:]],
        edgecolor="white", linewidth=0.5)
ax5.axhline(0, color="gray", linewidth=0.5)
ax5.set_xticks(range(len(names)))
ax5.set_xticklabels(names, rotation=22, ha="right", fontsize=7)
ax5.set_ylabel("% reduction"); ax5.set_title("Improvement vs baseline"); ax5.grid(axis="y", alpha=0.3)
for i, v in enumerate(impr):
    if v: ax5.text(i, v+0.3, f"{v:.1f}%", ha="center", fontsize=7)

plt.savefig("results/des_results.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nSaved: results/des_results.png")

rows = [{"Scenario":name,"Mean CT (min)":round(stat(r,"mean_ct")[0],1),
         "Mean CT (hrs)":round(stat(r,"mean_ct")[0]/60,2),
         "P95 CT (hrs)":round(stat(r,"p95_ct")[0]/60,2),
         "Utilisation (%)":round(stat(r,"utilisation")[0],1),
         "Mean queue":round(stat(r,"mean_queue")[0],2),
         "Trucks processed":round(stat(r,"n_trucks")[0],0)}
        for name, r in all_results.items()]
pd.DataFrame(rows).to_csv("results/kpi_summary.csv", index=False)
print("Saved: results/kpi_summary.csv")
print("Run sensitivity.py next.\n")