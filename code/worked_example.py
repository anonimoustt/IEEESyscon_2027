# Worked example of Section IV: how the thresholds are set, and how year 31 of MLP_Weather is judged.
# It reads the monitor outputs, so every number matches the paper (Tables VI and VII).
# Usage: python worked_example.py [MONITOR_DIR] [YEAR]      (defaults: results/monitor and 31)
import csv  # monitor tables
import json  # monitor summary
import os  # paths
import sys  # command line arguments

import numpy as np  # random draws of the first resampled year

MON = sys.argv[1] if len(sys.argv) > 1 else os.path.join("results", "monitor")  # monitor outputs
SHOW = sys.argv[2] if len(sys.argv) > 2 else "31"  # monitored year to explain
MODEL = "MLP_Weather"  # the network
s = json.load(open(os.path.join(MON, "monitor_summary_%s.json" % MODEL)))  # thresholds and settings
row = next(r for r in csv.DictReader(open(os.path.join(MON, "monitor_years_%s.csv" % MODEL))) if r["year"] == SHOW)  # year
PLAN = s["plan"]  # the ten metric kinds
HIGH_IS_GOOD = {"Accuracy", "F1_Score"}  # shown as scores; degraded when below the threshold
LINKS = {"Accuracy": "C", "F1_Score": "C", "Accuracy_Variance": "C, R", "MMD": "R",  # Fig. 2 links
         "KS": "R", "Unsafe_Output_Rate": "S", "Attack_Success_Rate": "Sec",  # Fig. 2 links
         "Prediction_Flip_Rate": "P", "Explanation_Stability": "P, T", "Explanation_Fidelity": "T"}  # Fig. 2 links


def show(m, v):  # value in the unit of the paper
    return 1 - v if m in HIGH_IS_GOOD else v  # accuracy and F1 as scores


# Step 1: what a resampled year is
g = np.random.default_rng([0, 200])  # the stream of the first run, as in ontology_monitor.py
pick = g.choice(60, 12, replace=True)  # 12 of the 60 months of years 6 to 10
print("First resampled year of the 200 run joins (year, month):",  # header
      ", ".join("(%d, %d)" % (6 + k // 12, k % 12 + 1) for k in pick))  # month k of the normal period

# Step 2: thresholds from four runs and their average
print("\nThresholds (95th percentile) of each run, their average, and the validation rate:")  # header
for m in PLAN:  # each metric
    runs = [show(m, s["threshold_runs"][B][m][0]) for B in ("200", "400", "800", "1600")]  # four runs
    avg = show(m, s["thresholds"][m][0])  # averaged threshold
    rate = 100.0 * s["validation"]["metric_degraded"][m] / s["validation"]["years"]  # crossed in validation years
    print("  %-22s %s  average %.4f  validation %.1f%%" % (m, "  ".join("%.4f" % v for v in runs), avg, rate))  # one line
print("  severe levels (99th percentile, averaged): MMD %.4f, KS %.4f" % (s["thresholds"]["MMD"][1], s["thresholds"]["KS"][1]))  # severe

# Step 3: one monitored year
print("\nYear %s = records %d to %d" % (SHOW, 360 * (int(SHOW) - 1) + 1, 360 * int(SHOW)))  # which days
print("  %-22s %8s %9s  %-9s %s" % ("metric", "value", "threshold", "result", "attributes"))  # header
for m in PLAN:  # each metric
    v, tau = show(m, float(row["v_" + m])), show(m, s["thresholds"][m][0])  # value and threshold
    severe = m in ("MMD", "KS") and float(row["v_" + m]) > s["thresholds"][m][1]  # beyond the severe level
    res = ("severe" if severe else "degraded") if row["deg_" + m] == "1" else "normal"  # step 1 of the rule
    att = {"normal": "", "degraded": LINKS[m], "severe": LINKS[m] + ", Res"}[res]  # attributes it degrades
    print("  %-22s %8.4f %9.4f  %-9s %s" % (m, v, tau, res, att))  # one line
attrs = [a for a in ("Correctness", "Reliability", "Safety", "Security", "Resilience", "Predictability",  # step 2
                     "Transparency_Interpretability") if row[a] == "1"]  # degraded attributes
print("  degraded attributes:", ", ".join(attrs) or "none")  # step 2 of the rule
for d in sorted(s["monitoring"]["debt"]):  # step 3 of the rule
    if row[d] != "none":  # complete pattern
        print("  %s: %s" % (d, {"detected": "detected by two or more metrics",  # outcome
                                "one_metric_only": "all attributes degraded, but by one metric only"}[row[d]]))  # outcome
for d in filter(None, row["ruled_out"].split(";")):  # complete pattern without history
    print("  %s: all attributes degraded, but ruled out (no fine tuning or transfer on record)" % d)  # outcome
