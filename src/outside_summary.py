"""One figure for the top of "Did outside factors cause this?": real-shop values next to ours.

Reads result tables written by external_factors.py and reference_compare.py (run those first).
Real-shop values come from the French bakery (claims real; Paris assumed) and the coffee vending machine
(claims real). Maven is self-described fictitious and is drawn with a hollow marker. Bars are 95% intervals
where the source table has one. Context only: nothing here says another shop's pattern causes ours.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import ROOT, save_fig

R = os.path.join(ROOT, "results")
tr = pd.read_csv(os.path.join(R, "reference_effect_transfer.csv"))
wc = pd.read_csv(os.path.join(R, "external_weather_coefficients.csv")).set_index("term")
wg = pd.read_csv(os.path.join(R, "external_weather_growth.csv")).iloc[0]
hs = pd.read_csv(os.path.join(R, "external_holidays_summary.csv")).iloc[0]
sig = pd.read_csv(os.path.join(R, "reference_signatures.csv")).set_index("dataset")
tb = pd.read_csv(os.path.join(R, "external_tuesday_by_branch.csv")).set_index("branch")

REAL, OURS, FICT = "#2c3e50", "#c0392b", "#7f8c8d"


def bakery(spec, effect):
    r = tr[(tr.spec == spec) & (tr.effect == effect)].iloc[0]
    return r.bakery_pct, r.bakery_ci_low, r.bakery_ci_high


MAIN, MONTH = "weekday + trend + weather + holiday", "same + month fixed effects"
panels = [
    ("Public holiday effect (%)", [
        ("French bakery", *bakery(MAIN, "public holiday"), REAL, "o"),
        ("Stories", 100 * (hs.mean_ratio - 1), 100 * (hs.ci_low - 1), 100 * (hs.ci_high - 1), OURS, "o")]),
    ("Temperature, within month (% per °C)", [
        ("French bakery", *bakery(MONTH, "per 1 degC of daily max temperature"), REAL, "o"),
        ("Stories", wg.within_month_tmax_coef_pct_per_degC, wg.within_month_tmax_ci_low, wg.within_month_tmax_ci_high, OURS, "o")]),
    ("Rain day effect (%)", [
        ("French bakery", *bakery(MAIN, "rain day (1 mm or more)"), REAL, "o"),
        ("Stories", wc.loc["rain_day", "effect_pct"], wc.loc["rain_day", "effect_ci_low_pct"], wc.loc["rain_day", "effect_ci_high_pct"], OURS, "o")]),
    ("Day-to-day variation (variance / mean)", [
        ("French bakery", sig.loc["French bakery (real)", "dispersion_ratio"], None, None, REAL, "o"),
        ("Vending machine", sig.loc["Vending machine (real)", "dispersion_ratio"], None, None, REAL, "o"),
        ("Maven (fictitious)", sig.loc["Maven (fictitious, NYC)", "dispersion_ratio"], None, None, FICT, "o_hollow"),
        ("Stories", sig.loc["Stories (ours)", "dispersion_ratio"], sig.loc["Stories (ours)", "poisson_range_low"],
         sig.loc["Stories (ours)", "poisson_range_high"], OURS, "o")]),
    ("Tuesday / Mon, Wed, Thu, Fri", [
        ("French bakery", sig.loc["French bakery (real)", "tue_ratio_vs_mon_wed_thu_fri"], None, None, REAL, "o"),
        ("Vending machine", sig.loc["Vending machine (real)", "tue_ratio_vs_mon_wed_thu_fri"], None, None, REAL, "o"),
        ("Maven (fictitious)", sig.loc["Maven (fictitious, NYC)", "tue_ratio_vs_mon_wed_thu_fri"], None, None, FICT, "o_hollow"),
        *[(f"Stories {b}", tb.loc[b, "tue_ratio"], tb.loc[b, "ci_low"], tb.loc[b, "ci_high"], OURS, "o")
          for b in ["Garden", "Harbour", "Uptown"]]]),
]
ref_line = {0: 0, 1: 0, 2: 0, 3: 1, 4: 1}

fig, axes = plt.subplots(1, 5, figsize=(20, 4.2))
for k, (ax, (title, rows)) in enumerate(zip(axes, panels)):
    for i, (label, v, lo, hi, col, mk) in enumerate(rows):
        hollow = mk == "o_hollow"
        if lo is not None:
            ax.errorbar(v, i, xerr=[[v - lo], [hi - v]], fmt="o", color=col, capsize=5, ms=7)
        else:
            ax.plot(v, i, "o", ms=8, color=col, mfc="white" if hollow else col)
    ax.axvline(ref_line[k], color="grey", ls="--", lw=0.8)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=8)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("Value (bars: 95% interval; Stories variation bar: pure-chance range)" if k == 3 else "Value (bars: 95% interval)", fontsize=8)
fig.suptitle("Real shops (dark) vs Stories (red): clear gaps on holidays, day-to-day variation and Tuesday; temperature borderline (intervals touch); rain cannot tell",
             fontsize=11)
fig.tight_layout()
save_fig(fig, "outside_factors_summary.png")
print("saved figures/outside_factors_summary.png")
