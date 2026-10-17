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


def main():
    if not os.path.exists(os.path.join(ROOT, "data", "stories_transactions.csv")):
        sys.exit("data/stories_transactions.csv is missing; see data/README.md")
    have_ref = all(os.path.isdir(os.path.join(REF_DIR, s)) and os.listdir(os.path.join(REF_DIR, s)) for s in REF_SETS)
    t_all = time.time()
    for script in SCRIPTS:
        if script == "reference_compare.py" and not have_ref:
            print(f"SKIP {script}: Kaggle reference datasets not found in data/external/reference/ "
                  "(see data/README.md); later scripts use the committed results/reference_*.csv")
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
        print(f"     ok in {time.time() - t0:.0f} s")
    print(f"all scripts finished in {time.time() - t_all:.0f} s")


if __name__ == "__main__":
    main()
