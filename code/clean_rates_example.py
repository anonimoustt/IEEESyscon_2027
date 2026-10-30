# Recomputes the validation rates of Table VI (27.5% and 2.9% for MLP_Weather, 20.3% and 2.3% for LR_Weather)
# from the metric values of the 5,000 validation years and the averaged thresholds, with the debt rule typed in.
# Usage: python clean_rates_example.py [REPO_DIR or -] [MLP_Weather or LR_Weather]   (- reads the files from GitHub)
import csv  # validation years
import io  # wrap downloaded text
import json  # thresholds
import os  # paths
import sys  # command line arguments
import urllib.request  # download from GitHub

RAW = "https://raw.githubusercontent.com/anonimoustt/IEEESyscon_2027/main/"  # repository files
MODEL = sys.argv[2] if len(sys.argv) > 2 else "MLP_Weather"  # model to recompute
YEARS = "results/monitor/monitor_validation_%s.csv" % MODEL  # 5,000 resampled years with their metric values
SUMMARY = "results/monitor/monitor_summary_%s.json" % MODEL  # averaged thresholds


def read(path):  # local file if a folder is given, else GitHub
    if len(sys.argv) > 1 and sys.argv[1] != "-":  # folder given
        return open(os.path.join(sys.argv[1], path)).read()  # local copy
    return urllib.request.urlopen(RAW + path).read().decode()  # GitHub copy


rows = list(csv.DictReader(io.StringIO(read(YEARS))))  # one row per validation year
TH = json.loads(read(SUMMARY))["thresholds"]  # metric: [threshold, severe level]
METRICS = [m for m in TH if "v_" + m in rows[0]]  # the metrics of this model
LINKS = {"Accuracy": {"C"}, "F1_Score": {"C"}, "Accuracy_Variance": {"C", "R"}, "MMD": {"R"}, "KS": {"R"},  # Fig. 2
         "Unsafe_Output_Rate": {"S"}, "Attack_Success_Rate": {"Sec"}, "Prediction_Flip_Rate": {"P"},  # Fig. 2
         "Explanation_Stability": {"P", "T"}, "Explanation_Fidelity": {"T"}}  # Fig. 2
SEVERE = {"MMD", "KS"}  # also degrade Resilience when severe
DEBTS = {"Source_Target_Mismatch": {"R", "P", "T"}, "Capability_Loss": {"C", "R"}, "Robustness_Debt": {"C", "Sec"},  # Table II
         "Operating_Envelope": {"R", "Res"}, "Harmful_Output": {"S", "Sec"}, "Faithfulness": {"P", "T"}}  # Table II
NEEDS_HISTORY = {"Source_Target_Mismatch", "Capability_Loss"}  # need a transfer or a fine tuning; neither model has one


def debt_rule(r):  # the three steps of the rule for one year
    deg = [m for m in METRICS if float(r["v_" + m]) > TH[m][0]]  # step 1: values are stored so that larger is worse
    ev = {m: LINKS[m] | ({"Res"} if m in SEVERE and float(r["v_" + m]) > TH[m][1] else set()) for m in deg}  # step 2
    attrs = set().union(*ev.values()) if ev else set()  # degraded attributes
    found = [d for d, need in DEBTS.items() if need <= attrs and d not in NEEDS_HISTORY  # step 3: all attributes
             and sum(bool(a & need) for a in ev.values()) >= 2]  # and two or more different metrics
    return deg, attrs, found  # outcome


n = len(rows)  # 5,000
one = sum(bool(debt_rule(r)[0]) for r in rows)  # one or more metrics degraded
two = sum(len(debt_rule(r)[0]) >= 2 for r in rows)  # two or more metrics, related or not
debt = sum(bool(debt_rule(r)[2]) for r in rows)  # a debt detected
for r in rows[:3]:  # three example years
    deg, attrs, found = debt_rule(r)  # apply the rule
    print("validation year %s: degraded %s; attributes %s; debt %s" % (r["year"], deg or "none",  # one line
                                                                        sorted(attrs) or "none", found or "none"))  # outcome
print("%s, %d validation years" % (MODEL, n))  # header
print("  any one metric degraded : %d = %.1f%%" % (one, 100.0 * one / n))  # 27.5% or 20.3%
print("  any two metrics degraded: %d = %.1f%%" % (two, 100.0 * two / n))  # 11.6% or 10.7%
print("  debt detected           : %d = %.1f%%" % (debt, 100.0 * debt / n))  # 2.9% or 2.3%
