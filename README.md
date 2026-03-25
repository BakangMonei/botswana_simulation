# Botswana Border Clearance Simulation

**IMB511 Final Year Project — University of Botswana**  
Simulation of Supply Chain Risk in Export Logistics: Lessons from Botswana's Negative Trade Balance

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Project Structure](#2-project-structure)
3. [Setup — macOS](#3-setup--macos)
4. [Setup — Windows](#4-setup--windows)
5. [Setup — Linux](#5-setup--linux)
6. [Running the Simulation](#6-running-the-simulation)
7. [How the Code Works](#7-how-the-code-works)
8. [How to Change Inputs](#8-how-to-change-inputs)
9. [Understanding the Outputs](#9-understanding-the-outputs)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Project Overview

This project simulates truck clearance at Botswana's export border posts (Tlokweng, Kazungula, Ramokgwebana) using two simulation techniques:

- **Monte Carlo Simulation (MCS)** — runs 10,000 trials to estimate the probability distribution of clearance times under uncertainty
- **Discrete Event Simulation (DES)** — models the actual step-by-step queue process a truck goes through, using SimPy
- **Sensitivity Analysis** — identifies which input parameters have the greatest impact on clearance time

The simulation tests five scenarios:

| Scenario          | What changes                                 |
| ----------------- | -------------------------------------------- |
| Baseline          | Current system — no changes                  |
| S1: 24-hr ops     | Border open 24 hours, 4 servers instead of 2 |
| S2: ICT upgrade   | ICT failure probability drops from 24% to 5% |
| S3: Pre-clearance | Document error rate drops from 26% to 8%     |
| S4: Combined      | All three improvements applied together      |

**Key Performance Indicators (KPIs) measured:**

- Mean clearance time (minutes / hours)
- 95th percentile clearance time
- Server utilisation (%)
- Mean queue length (trucks)
- Throughput (trucks processed per simulation run)

---

## 2. Project Structure

```
botswana_simulation/
│
├── monte_carlo.py          # File 1 — Monte Carlo simulation (run first)
├── des_model.py            # File 2 — Discrete Event Simulation (run second)
├── sensitivity.py          # File 3 — Sensitivity / tornado analysis (run third)
│
├── results/                # Auto-created when you run any script
│   ├── monte_carlo_results.png
│   ├── des_results.png
│   ├── sensitivity_results.png
│   └── kpi_summary.csv
│
├── venv/                   # Virtual environment (created during setup)
└── README.md               # This file
```

---

## 3. Setup — macOS

### Step 1 — Open Terminal

Press **⌘ + Space**, type `Terminal`, press Enter.

### Step 2 — Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Enter your Mac password when prompted (nothing will appear as you type — that is normal).

> **Apple Silicon Macs (M1/M2/M3):** After Homebrew installs, it will print two commands starting with `export PATH=...` — run both of them before continuing.

### Step 3 — Install Python

```bash
brew install python
python3 --version    # Should show Python 3.11 or higher
```

### Step 4 — Create the project folder

```bash
cd ~/Desktop
mkdir botswana_simulation
cd botswana_simulation
```

### Step 5 — Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

Your Terminal prompt will now show `(venv)` at the start.

### Step 6 — Install all required libraries

```bash
pip install numpy scipy matplotlib pandas simpy seaborn
```

### Step 7 — Install VS Code (recommended editor)

Download from: https://code.visualstudio.com/download

Choose **macOS (Apple Silicon)** for M1/M2/M3 Macs, or **macOS (Intel)** for older Macs.

After installing, open VS Code and install the Python extension:  
**⌘+Shift+X** → search `Python` → install the Microsoft extension.

### Step 8 — Open the project in VS Code

```bash
code .
```

Then select your interpreter: **⌘+Shift+P** → `Python: Select Interpreter` → choose the one with `venv` in the path.

> **Every time you open a new Terminal session**, you must re-activate the venv:
>
> ```bash
> cd ~/Desktop/botswana_simulation
> source venv/bin/activate
> ```

---

## 4. Setup — Windows

### Step 1 — Install Python

Go to https://www.python.org/downloads/ and download the latest Python 3.x installer.

During installation, **check the box "Add Python to PATH"** before clicking Install. This is critical.

Verify it worked — open **Command Prompt** (search for `cmd` in Start menu):

```cmd
python --version
pip --version
```

### Step 2 — Create the project folder

```cmd
cd %USERPROFILE%\Desktop
mkdir botswana_simulation
cd botswana_simulation
```

### Step 3 — Create and activate a virtual environment

```cmd
python -m venv venv
venv\Scripts\activate
```

Your prompt will now show `(venv)` at the start.

> If you get a permissions error on `activate`, run this first:
>
> ```cmd
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
>
> Then try `venv\Scripts\activate` again.

### Step 4 — Install all required libraries

```cmd
pip install numpy scipy matplotlib pandas simpy seaborn
```

### Step 5 — Install VS Code

Download from: https://code.visualstudio.com/download — choose the **Windows** installer.

After installing, open VS Code and install the Python extension:  
**Ctrl+Shift+X** → search `Python` → install the Microsoft extension.

### Step 6 — Open the project in VS Code

```cmd
code .
```

Select your interpreter: **Ctrl+Shift+P** → `Python: Select Interpreter` → choose the one with `venv` in the path.

> **Every time you open a new Command Prompt**, re-activate the venv:
>
> ```cmd
> cd %USERPROFILE%\Desktop\botswana_simulation
> venv\Scripts\activate
> ```

---

## 5. Setup — Linux (Ubuntu / Debian)

### Step 1 — Open Terminal

Press **Ctrl+Alt+T**.

### Step 2 — Install Python and pip

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
python3 --version    # Should show 3.10 or higher
```

### Step 3 — Create the project folder

```bash
cd ~/Desktop
mkdir botswana_simulation
cd botswana_simulation
```

### Step 4 — Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 5 — Install all required libraries

```bash
pip install numpy scipy matplotlib pandas simpy seaborn
```

### Step 6 — Install VS Code (optional but recommended)

```bash
sudo snap install code --classic
```

Or download from: https://code.visualstudio.com/download

> **Every time you open a new Terminal**, re-activate the venv:
>
> ```bash
> cd ~/Desktop/botswana_simulation
> source venv/bin/activate
> ```

---

## 6. Running the Simulation

Make sure your virtual environment is active (you see `(venv)` in your prompt) and you are inside the `botswana_simulation` folder. Then run the three files in order:

### Run File 1 — Monte Carlo

```bash
python3 monte_carlo.py        # macOS / Linux
python  monte_carlo.py        # Windows
```

- Runs 10,000 simulations per scenario (takes ~20–30 seconds)
- Prints a results table to the terminal
- Opens a chart window — **close it** to let the script finish
- Saves `results/monte_carlo_results.png`

### Run File 2 — Discrete Event Simulation

```bash
python3 des_model.py          # macOS / Linux
python  des_model.py          # Windows
```

- Runs 30 replications per scenario (takes ~30–60 seconds)
- Prints KPI table and Little's Law validation to terminal
- Opens a chart window — **close it** to let the script finish
- Saves `results/des_results.png` and `results/kpi_summary.csv`

### Run File 3 — Sensitivity Analysis

```bash
python3 sensitivity.py        # macOS / Linux
python  sensitivity.py        # Windows
```

- Runs 5,000 trials per parameter combination (takes ~30–45 seconds)
- Prints tornado table to terminal
- Opens a chart window — **close it** to let the script finish
- Saves `results/sensitivity_results.png`

### Run all three at once (macOS / Linux only)

```bash
python3 monte_carlo.py && python3 des_model.py && python3 sensitivity.py
```

---

## 7. How the Code Works

### monte_carlo.py — How it works

The Monte Carlo simulation models a single truck passing through all 6 stages of border clearance. It runs this simulation 50 times (one day of trucks) and records the average clearance time. It then repeats this 10,000 times to build a probability distribution.

**Stage flow for each truck:**

```
Truck arrives
    → Stage 1: Queue wait        (depends on arrival rate and number of servers)
    → Stage 2: Document check    (10–60 min, Triangular distribution)
         → If error (26%): secondary inspection (+45–120 min)
    → Stage 3: ICT processing    (10–40 min, Triangular)
         → If ICT fails (24%): restoration delay (Exponential, mean=45 min)
    → Stage 4: Physical scan     (20–50 min if scanner working)
         → If scanner broken (14%): manual inspection (60–180 min)
    → Stage 5: Agency coordination
         → If coordination delay (36%): +20–120 min
    → Truck exits — clearance time recorded
```

Each scenario changes the **probability values** feeding into these decisions. The simulation re-runs with the new values.

### des_model.py — How it works

The DES model uses **SimPy**, a Python process-based simulation library. Unlike Monte Carlo (which estimates distributions), SimPy actually simulates time passing, trucks queuing, and servers becoming busy or free.

Key SimPy concepts used:

- `simpy.Environment()` — the simulation clock
- `simpy.Resource(env, capacity=N)` — a server with N slots (customs officers, scanners)
- `yield env.timeout(duration)` — makes the truck wait for a service to complete
- `with resource.request() as req: yield req` — truck joins the queue and waits for a free slot

The simulation runs for 16 simulated hours, 30 times (replications). Results are averaged across all 30 runs with 95% confidence intervals.

**Little's Law** is used for validation: L = λ × W, where:

- L = average number of trucks in the system
- λ = average arrival rate (trucks per minute)
- W = average time spent in the system (mean clearance time)

### sensitivity.py — How it works

Sensitivity analysis varies one parameter at a time while keeping all others at their baseline values, then measures the change in mean clearance time. The results are displayed as a **tornado chart** — parameters with the largest swing (most impact) appear at the top.

A second test varies all parameters simultaneously (Monte Carlo over the parameter space) to show the full range of possible outcomes under uncertainty.

---

## 8. How to Change Inputs

All key inputs are clearly defined at the top of each file. You do not need to understand the full code to change them.

### Change baseline probabilities (monte_carlo.py and des_model.py)

In `monte_carlo.py`, find the `simulate_one_truck` function. The baseline values are:

```python
# Stage 2: Document error probability
doc_error_prob = 0.26          # 26% of trucks have document errors
                               # Change to: 0.10 for 10%, 0.40 for 40%, etc.

# Stage 3: ICT failure probability
ict_fail_prob = 0.24           # 24% chance of ICT downtime per truck
ict_restore_mean = 45          # Average restoration time in minutes

# Stage 4: Scanner availability
scanner_ok = 0.86              # 86% chance scanner is working
                               # Change to: 0.95 for better scanner, 0.70 for worse

# Stage 5: Coordination delay probability
coord_prob = 0.36              # 36% of trucks experience coordination delays
```

### Change scenario parameters

In `des_model.py`, find the `SCENARIOS` dictionary near the top:

```python
SCENARIOS = {
    "Baseline": dict(
        servers      = 2,      # Number of customs officers/lanes
        ict_fail     = 0.24,   # ICT failure probability
        ict_restore  = 45,     # ICT restoration time (minutes)
        doc_error    = 0.26,   # Document error probability
        coord_prob   = 0.36,   # Coordination delay probability
        scanner_ok   = 0.86,   # Scanner availability
        arrival_rate = 12      # Trucks arriving per hour
    ),
    "S1: 24-hr ops": dict(
        servers      = 4,      # More servers for extended hours
        arrival_rate = 8,      # Spread over more hours = lower peak rate
        # ... all other values same as baseline
    ),
    # Add your own scenario here:
    "My Scenario": dict(
        servers      = 3,      # Try 3 servers
        ict_fail     = 0.10,   # Improved ICT
        ict_restore  = 20,
        doc_error    = 0.15,
        coord_prob   = 0.25,
        scanner_ok   = 0.92,
        arrival_rate = 12
    ),
}
```

Just add a new entry to the dictionary and it will be included in all charts and tables automatically.

### Change simulation size / speed

In `monte_carlo.py`:

```python
N_SIMULATIONS = 10000   # Reduce to 1000 for faster runs during testing
N_TRUCKS = 50           # Trucks simulated per day — increase for more accuracy
```

In `des_model.py`:

```python
SIM_HOURS      = 16     # How many simulated hours per replication
N_REPLICATIONS = 30     # Number of independent runs — minimum 30 for statistics
```

### Change service time distributions

Service times use statistical distributions. To change them, find the relevant line and adjust the parameters:

```python
# Triangular distribution: triangular(minimum, most_likely, maximum)
np.random.triangular(10, 25, 60)    # Document check: min=10min, mode=25min, max=60min
np.random.triangular(10, 20, 40)    # ICT processing
np.random.triangular(20, 60, 120)   # Coordination delay

# Uniform distribution: uniform(minimum, maximum)
np.random.uniform(45, 120)          # Secondary inspection
np.random.uniform(20, 50)           # Physical scan (scanner working)
np.random.uniform(60, 180)          # Physical scan (manual, scanner broken)

# Exponential distribution: exponential(mean)
np.random.exponential(45)           # ICT restoration time, mean=45 minutes
```

### Change sensitivity analysis ranges

In `sensitivity.py`, find the `params` dictionary:

```python
params = {
    #          parameter key    low value   high value
    "Doc error prob":   ("doc_error",    0.08,  0.50),
    "ICT failure prob": ("ict_fail",     0.05,  0.50),
    "Coord delay prob": ("coord_prob",   0.10,  0.60),
    "Scanner avail":    ("scanner_ok",   0.70,  0.99),
    "ICT restore (min)":("ict_restore",  10,    90),
    "Arrival rate":     ("arrival_rate", 8,     16),
    "Servers":          ("servers",      1,     4),
}
```

Change the low and high values to adjust the range tested for each parameter.

---

## 9. Understanding the Outputs

### Terminal output — what the numbers mean

```
Scenario               Mean (hrs)  P95 (hrs)  vs Baseline
----------------------------------------------------------
Baseline                     7.64       8.88           —
S1: 24-hr ops                3.08       3.37       -59.7%
S2: ICT upgrade              7.31       8.53        -4.2%
S3: Pre-clearance            7.14       8.40        -6.5%
S4: Combined                 2.27       2.47       -70.3%
```

- **Mean (hrs)** — the average clearance time across all simulation runs
- **P95 (hrs)** — 95% of trucks clear in this time or less (worst-case planning value)
- **vs Baseline** — percentage improvement compared to the current system

### Chart outputs

| File                      | What it shows                                                                             |
| ------------------------- | ----------------------------------------------------------------------------------------- |
| `monte_carlo_results.png` | Distribution curves for each scenario + bar chart with confidence intervals               |
| `des_results.png`         | Six KPI charts: clearance time, utilisation, queue length, P95, improvement %, throughput |
| `sensitivity_results.png` | Tornado chart (which parameters matter most) + full uncertainty distribution              |

### kpi_summary.csv

A spreadsheet-ready table with all KPIs for every scenario. Open in Excel or Google Sheets. Use this table directly in your report for Chapter 4.

### Little's Law validation table

```
Scenario         λ(tr/hr)   W(min)     L=λW   L_queue   Check
---------------------------------------------------------------
Baseline             1.05    483.3     8.47     76.86    PASS
```

- **λ** = observed throughput (trucks per hour)
- **W** = mean time in system (minutes)
- **L = λW** = expected trucks in system (Little's Law)
- **L_queue** = observed average queue length
- **PASS** = L_system > L_queue (mathematically required — validates model logic)

---

## 10. Troubleshooting

### `ModuleNotFoundError: No module named 'simpy'`

Your virtual environment is not active. Run:

```bash
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows
```

Then re-run the script.

### `python3: command not found` (Windows)

Use `python` instead of `python3` on Windows:

```cmd
python monte_carlo.py
```

### Chart window freezes / does not close

Click the X button on the chart window, or press **Q** while the chart is in focus.

### `pip: command not found`

```bash
python3 -m pip install numpy scipy matplotlib pandas simpy seaborn
```

### Permission denied when activating venv (Windows PowerShell)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Simulation runs but produces no chart (headless server / SSH)

Add this line at the top of the script, before the `import matplotlib.pyplot` line:

```python
import matplotlib
matplotlib.use('Agg')
```

Charts will save to the `results/` folder without displaying.

### `code .` command not found (VS Code)

Open VS Code manually, press **⌘+Shift+P** (Mac) or **Ctrl+Shift+P** (Windows/Linux), type `Shell Command: Install 'code' command in PATH`, press Enter, then try `code .` again.

---

## Requirements

| Library    | Version    | Purpose                          |
| ---------- | ---------- | -------------------------------- |
| Python     | 3.10+      | Runtime                          |
| numpy      | any recent | Random distributions, statistics |
| scipy      | any recent | Statistical functions            |
| matplotlib | any recent | All charts and plots             |
| pandas     | any recent | KPI table, CSV export            |
| simpy      | 4.x        | Discrete Event Simulation engine |
| seaborn    | any recent | Chart styling                    |

Install all at once:

```bash
pip install numpy scipy matplotlib pandas simpy seaborn
```

---

_University of Botswana — Department of Mechanical Engineering (Industrial Engineering)_  
_Supervised by Dr. Kobamelo Mashaba_  
_Larona Waren Kgotso (202001460) & Tiroyaone Ditsele (202000542)_
