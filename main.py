#!/usr/bin/env python3
"""
Botswana border clearance — unified dashboard.

  Interactive UI (default):  python main.py
                             → starts Streamlit in your browser

  Batch / terminal only:     python main.py --cli
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

RESULTS_DIR = "results"
_UI_FLAG = "BOTS_SIM_UI"


def _project_css() -> str:
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Fraunces', Georgia, serif !important; letter-spacing: -0.02em; }
    .block-container { padding-top: 2rem; max-width: 1200px; }
    div[data-testid="stMetricValue"] { font-family: 'Fraunces', Georgia, serif; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .highlight-box {
        padding: 1rem 1.25rem;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(29,158,117,0.08) 0%, rgba(24,95,165,0.08) 100%);
        border: 1px solid rgba(29,158,117,0.25);
        margin-bottom: 1rem;
    }
    </style>
    """


def run_full_pipeline(
    *,
    seed: int,
    mc_sims: int,
    mc_trucks: int,
    des_hours: float,
    des_reps: int,
    sens_samples: int,
    sens_base: dict,
    progress=None,
) -> dict:
    """Run Monte Carlo → DES → sensitivity. Optional Streamlit progress tuple (container, bar)."""
    from monte_carlo import run_monte_carlo
    from des_model import run_des
    from sensitivity import run_sensitivity

    def tick(msg: str, frac: float):
        if progress:
            progress[0].text(msg)
            progress[1].progress(frac)

    tick("Monte Carlo simulation…", 0.05)
    mc = run_monte_carlo(
        n_simulations=mc_sims,
        n_trucks=mc_trucks,
        seed=seed,
        results_dir=RESULTS_DIR,
        show_plot=False,
        save=True,
    )
    tick("Discrete-event simulation (SimPy)…", 0.4)
    des = run_des(
        sim_hours=des_hours,
        n_replications=des_reps,
        base_seed=seed,
        results_dir=RESULTS_DIR,
        show_plot=False,
        save=True,
    )
    tick("Sensitivity analysis…", 0.72)
    sens = run_sensitivity(
        n_samples=sens_samples,
        seed=seed,
        base=sens_base,
        results_dir=RESULTS_DIR,
        show_plot=False,
        save=True,
    )
    tick("Done.", 1.0)
    return {"monte_carlo": mc, "des": des, "sensitivity": sens}


def main_cli() -> None:
    """Run all three models once with defaults (no browser)."""
    from monte_carlo import print_summary, run_monte_carlo
    from des_model import print_des_tables, run_des
    from sensitivity import print_sensitivity_report, run_sensitivity
    from sensitivity import DEFAULT_BASE

    seed = 42
    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 72)
    print("  BOTSWANA BORDER CLEARANCE — FULL PIPELINE (CLI)")
    print("=" * 72)

    print("\n--- Monte Carlo ---")
    mc = run_monte_carlo(seed=seed, results_dir=RESULTS_DIR, show_plot=False, save=True)
    print_summary(mc["summary"])
    print(f"Saved: {mc['figure_path']}")

    print("\n--- Discrete-event simulation ---")
    des = run_des(base_seed=seed, results_dir=RESULTS_DIR, show_plot=False, save=True)
    print_des_tables(des["all_results"])
    print(f"Saved: {des['figure_path']}")
    print(f"Saved: {des['csv_path']}")

    print("\n--- Sensitivity ---")
    sens = run_sensitivity(
        seed=seed, base=DEFAULT_BASE, results_dir=RESULTS_DIR, show_plot=False, save=True
    )
    print_sensitivity_report(sens)
    print(f"Saved: {sens['figure_path']}")

    print("\nAll outputs in ./results/")
    print("For the interactive UI:  python main.py  (no --cli)\n")


def main_streamlit() -> None:
    import pandas as pd
    import streamlit as st

    st.set_page_config(
        page_title="Botswana Border Simulation",
        page_icon="🚛",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_project_css(), unsafe_allow_html=True)

    st.title("Botswana border clearance simulation")
    st.markdown(
        '<p class="highlight-box"><strong>Monte Carlo</strong>, <strong>discrete-event (SimPy)</strong>, '
        "and <strong>sensitivity</strong> models in one place. Adjust parameters in the sidebar, "
        "then run the pipeline to refresh charts and KPIs.</p>",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Simulation controls")
        seed = st.number_input("Random seed", min_value=0, max_value=999_999, value=42, step=1)
        st.subheader("Monte Carlo")
        mc_sims = st.slider("Daily replications", 500, 20_000, 10_000, 500)
        mc_trucks = st.slider("Trucks per replication", 5, 100, 50, 5)
        st.subheader("Discrete-event (DES)")
        des_hours = st.slider("Simulation horizon (hours)", 4.0, 24.0, 16.0, 1.0)
        des_reps = st.slider("DES replications", 5, 80, 30, 5)
        st.subheader("Sensitivity — baseline point")
        d_doc = st.slider("Doc error probability", 0.05, 0.50, 0.26, 0.01)
        d_ict = st.slider("ICT failure probability", 0.05, 0.50, 0.24, 0.01)
        d_coord = st.slider("Coordination delay probability", 0.10, 0.60, 0.36, 0.01)
        d_scan = st.slider("Scanner success probability", 0.70, 0.99, 0.86, 0.01)
        d_restore = st.slider("ICT restore mean (minutes)", 5.0, 120.0, 45.0, 1.0)
        d_arr = st.slider("Arrival rate (trucks/hour)", 4.0, 20.0, 12.0, 0.5)
        d_srv = st.slider("Customs servers (baseline)", 1, 6, 2, 1)
        st.subheader("Sensitivity — sample size")
        sens_samples = st.slider("Sensitivity MC samples", 500, 15_000, 5000, 500)

        run = st.button("Run full pipeline", type="primary", use_container_width=True)

    sens_base = {
        "doc_error": d_doc,
        "ict_fail": d_ict,
        "coord_prob": d_coord,
        "scanner_ok": d_scan,
        "ict_restore": d_restore,
        "arrival_rate": d_arr,
        "servers": int(d_srv),
    }

    if not run and "last_run" not in st.session_state:
        st.info("Set parameters in the sidebar and click **Run full pipeline** to generate results.")
        if Path(RESULTS_DIR, "monte_carlo_results.png").exists():
            st.caption("Showing last saved images from `results/` (run again to refresh).")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.image(str(Path(RESULTS_DIR) / "monte_carlo_results.png"), caption="Monte Carlo")
            with c2:
                st.image(str(Path(RESULTS_DIR) / "des_results.png"), caption="DES")
            with c3:
                st.image(str(Path(RESULTS_DIR) / "sensitivity_results.png"), caption="Sensitivity")
        return

    if run:
        status = st.empty()
        bar = st.progress(0.0)
        try:
            out = run_full_pipeline(
                seed=int(seed),
                mc_sims=int(mc_sims),
                mc_trucks=int(mc_trucks),
                des_hours=float(des_hours),
                des_reps=int(des_reps),
                sens_samples=int(sens_samples),
                sens_base=sens_base,
                progress=(status, bar),
            )
        except Exception as e:
            status.empty()
            bar.empty()
            st.error(f"Simulation failed: {e}")
            raise
        status.empty()
        bar.empty()
        st.session_state["last_run"] = out
        st.toast("Pipeline finished — charts updated.", icon="✅")

    out = st.session_state.get("last_run")
    if not out:
        return

    mc, des, sens = out["monte_carlo"], out["des"], out["sensitivity"]

    st.subheader("Key metrics")
    m1, m2, m3, m4 = st.columns(4)
    baseline_mc = next(x for x in mc["summary"] if x["Scenario"] == "Baseline")
    with m1:
        st.metric("MC baseline mean", f"{baseline_mc['Mean (hrs)']} h")
    with m2:
        st.metric("MC baseline P95", f"{baseline_mc['P95 (hrs)']} h")
    with m3:
        s = sens["summary"]
        st.metric("Sens. baseline mean", f"{s['baseline_mean_hrs']:.2f} h")
    with m4:
        st.metric("Uncertainty P95", f"{s['mc_p95_hrs']:.2f} h")

    st.subheader("Charts")
    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        st.image(mc["figure_path"], caption="Monte Carlo distributions")
    with ic2:
        st.image(des["figure_path"], caption="DES KPIs")
    with ic3:
        st.image(sens["figure_path"], caption="Sensitivity / tornado")

    with st.expander("Monte Carlo summary table", expanded=False):
        st.dataframe(pd.DataFrame(mc["summary"]), use_container_width=True, hide_index=True)

    with st.expander("DES — Little's law check", expanded=False):
        st.dataframe(pd.DataFrame(des["littles"]), use_container_width=True, hide_index=True)

    with st.expander("Sensitivity — tornado (minutes)", expanded=False):
        st.dataframe(
            pd.DataFrame(sens["summary"]["tornado_table"]),
            use_container_width=True,
            hide_index=True,
        )

    csv_p = des.get("csv_path")
    if csv_p and Path(csv_p).exists():
        st.download_button(
            label="Download KPI summary (CSV)",
            data=Path(csv_p).read_bytes(),
            file_name="kpi_summary.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    if "--cli" in sys.argv:
        main_cli()
    elif os.environ.get(_UI_FLAG):
        main_streamlit()
    else:
        try:
            import streamlit  # noqa: F401
        except ImportError:
            print("Streamlit is required for the UI. Install with:")
            print("  python -m pip install -r requirements.txt")
            raise SystemExit(1) from None
        env = os.environ.copy()
        env[_UI_FLAG] = "1"
        rc = subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                __file__,
                "--browser.gatherUsageStats=false",
            ],
            env=env,
            cwd=os.path.dirname(os.path.abspath(__file__)) or ".",
        )
        raise SystemExit(rc)
