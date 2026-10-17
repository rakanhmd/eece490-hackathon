"""Run every analysis script in the README's order; stop at the first failure.

Usage (from the repo root, with data/stories_transactions.csv in place):
    python run_all.py

reference_compare.py needs the Kaggle reference datasets in data/external/reference/ (download commands in
data/README.md). If they are missing it is skipped with a message, and the two scripts that read its outputs
(weather_power.py, outside_summary.py) use the committed results/reference_*.csv tables; if those are missing too,
they are skipped as well.
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
SCRIPTS = [
    "margin_analysis.py", "pricing_analysis.py", "tuesday_check.py", "tuesday_decompose.py", "tuesday_mechanism.py",
    "weekend_check.py", "forecast.py", "promo_analysis.py", "discount_analysis.py", "basket_analysis.py",
    "external_factors.py", "benchmarks.py", "garden_cost_cause.py", "reference_compare.py", "weather_power.py",
    "outside_summary.py", "opportunity_estimates.py", "daypart_analysis.py", "customer_model.py", "staffing.py",
    "menu_profit.py", "experiment_power.py",
]
REF_DIR = os.path.join(ROOT, "data", "external", "reference")
REF_SETS = ["ahmedabbas757_coffee-sales", "matthieugimbert_french-bakery-daily-sales", "ihelon_coffee-sales"]
REF_OUTPUTS = [os.path.join(ROOT, "results", f) for f in ("reference_effect_transfer.csv", "reference_signatures.csv")]
NEEDS_REF = {"weather_power.py", "outside_summary.py"}
# Files each script must (re)write; checked after the script runs (path relative to the repo root).
EXPECTED = {
    "margin_analysis.py": ["results/margin_by_branch.csv", "results/unit_cost_ratio_by_product.csv"],
    "pricing_analysis.py": ["results/pricing_scenarios.csv", "results/pricing_structure.csv", "results/garden_cost_price_combined.csv"],
    "tuesday_check.py": ["results/tuesday_weekday_ratios.csv", "results/tuesday_tx_per_day.csv"],
    "tuesday_decompose.py": ["results/tuesday_decomp_shares.csv"],
    "tuesday_mechanism.py": ["results/tuesday_mechanism.csv"],
    "weekend_check.py": ["results/weekend_weekly.csv"],
    "forecast.py": ["results/forecast_rolling_mae.csv", "results/forecast_rolling_bootstrap.csv", "results/forecast_mae.csv"],
    "promo_analysis.py": ["results/promo_did.csv", "results/promo_value.csv"],
    "discount_analysis.py": ["results/discount_cost.csv", "results/discount_spread.csv"],
    "basket_analysis.py": ["results/basket_value_scenarios.csv", "results/basket_attach_rates.csv", "results/basket_attach_primary_drink_sensitivity.csv"],
    "external_factors.py": ["results/external_factors_summary.csv", "results/external_weather_robust.csv"],
    "benchmarks.py": ["results/benchmarks_comparison.csv"],
    "garden_cost_cause.py": ["results/garden_cause_ratio_spread.csv"],
    "reference_compare.py": ["results/reference_signatures.csv", "results/reference_effect_transfer.csv"],
    "weather_power.py": ["results/external_weather_power.csv"],
    "outside_summary.py": ["figures/outside_factors_summary.png"],
    "opportunity_estimates.py": ["results/decision_thresholds.csv", "results/opportunity_saturday_range.csv"],
    "daypart_analysis.py": ["results/daypart_evening_dessert_total.csv"],
    "customer_model.py": ["results/customer_churn_test.csv", "results/customer_churn_origins.csv"],
    "staffing.py": ["results/staffing_rolling_results.csv", "results/staffing_break_sensitivity.csv"],
    "menu_profit.py": ["results/menu_products.csv", "results/menu_contribution.csv"],
    "experiment_power.py": ["results/experiment_power_results.csv", "results/experiment_discount_noninferiority.csv",
                            "results/experiment_duration_80pct.csv"],
}


def key_checks():
    """Recompute a few headline numbers from the results tables and compare with the README."""
    import pandas as pd
    R = os.path.join(ROOT, "results")
    comb = pd.read_csv(os.path.join(R, "garden_cost_price_combined.csv")).set_index("elasticity")
    fr = pd.read_csv(os.path.join(R, "forecast_rolling_mae.csv")).set_index("model")
    tr = pd.read_csv(os.path.join(R, "tuesday_weekday_ratios.csv"), index_col=0)
    dc = pd.read_csv(os.path.join(R, "discount_cost.csv"))
    th = pd.read_csv(os.path.join(R, "decision_thresholds.csv"))
    mb = pd.read_csv(os.path.join(R, "margin_by_branch.csv"), index_col=0)
    checks = [
        ("Garden cost fix, six months (USD)", round(float(comb.loc[-1.0, "cost_only_6mo_usd"])), 15888),
        ("Rolling forecast MAE, weekday + log trend", round(float(fr.loc["weekday_logtrend", "mae_all"]), 2), 6.39),
        ("Rolling forecast MAE, seasonal naive", round(float(fr.loc["seasonal_naive", "mae_all"]), 2), 8.79),
        ("Tuesday / mean(Mon, Wed, Thu, Fri), all branches", round(float(tr.loc["Tue", "all"]), 2), 1.53),
        ("10% discount given, six months (USD)", round(float(dc.discount_usd_jan_jun.iloc[0])), 1706),
        ("Garden recovery share at which the cost fix beats Option A (%)", round(100 * float(th.threshold.iloc[0]), 1), 51.0),
    ]
    gm = [c for c in mb.columns if "margin" in c.lower()]
    if gm:
        v = float(mb.loc["Garden", gm[0]])
        checks.append(("Garden gross margin (%)", round(100 * v if v < 1 else v, 1), 46.9))
    bad = 0
    print("\nKEY NUMBERS (results tables vs README):")
    for name, got, want in checks:
        ok = got == want
        bad += not ok
        print(f"  {'ok ' if ok else 'BAD'}  {name}: {got} (README {want})")
    return bad


def main():
    if not os.path.exists(os.path.join(ROOT, "data", "stories_transactions.csv")):
        sys.exit("data/stories_transactions.csv is missing; see data/README.md")
    have_ref = all(os.path.isdir(os.path.join(REF_DIR, s)) and os.listdir(os.path.join(REF_DIR, s)) for s in REF_SETS)
    t_all = time.time()
    fallback = []
    for script in SCRIPTS:
        if script == "reference_compare.py" and not have_ref:
            print(f"SKIP {script}: Kaggle reference datasets not found in data/external/reference/ "
                  "(see data/README.md)")
            if all(os.path.exists(p) for p in REF_OUTPUTS):
                print("     USING COMMITTED FALLBACK TABLES: " + ", ".join(os.path.relpath(p, ROOT) for p in REF_OUTPUTS))
                fallback += [os.path.relpath(p, ROOT) for p in REF_OUTPUTS]
            continue
        if script in NEEDS_REF and not have_ref and not all(os.path.exists(p) for p in REF_OUTPUTS):
            print(f"SKIP {script}: needs reference_compare.py outputs, which are missing")
            continue
        t0 = time.time()
        print(f"RUN  {script} ...", flush=True)
        r = subprocess.run([sys.executable, script], cwd=SRC, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-3000:])
            print(r.stderr[-3000:])
            sys.exit(f"FAILED: {script} (exit code {r.returncode}); stopping")
        stale = [f for f in EXPECTED.get(script, []) if not os.path.exists(os.path.join(ROOT, f))
                 or os.path.getmtime(os.path.join(ROOT, f)) < t0 - 1]
        if stale:
            sys.exit(f"FAILED: {script} ran but did not write {', '.join(stale)}; stopping")
        print(f"     ok in {time.time() - t0:.0f} s; wrote {len(EXPECTED.get(script, []))} expected file(s)")
    print(f"\nall scripts finished in {time.time() - t_all:.0f} s")
    if fallback:
        print("NOTE: these tables were NOT regenerated in this run (committed fallback): " + ", ".join(fallback))
    if key_checks():
        sys.exit("FAILED: a key number in the results tables differs from the README")


if __name__ == "__main__":
    main()
