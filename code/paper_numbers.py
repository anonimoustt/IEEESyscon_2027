# Computes every weather number quoted in Section IV of the paper (Tables IV to VI) from the monitor outputs.
# Usage: python paper_numbers.py MONITOR_DIR OUT_JSON [DATA_DIR]
import csv  # monitor tables
import json  # summaries and output
import os  # paths
import sys  # command line arguments

MON, OUT = sys.argv[1:3]  # inputs and output
DATA = sys.argv[3] if len(sys.argv) > 3 else None  # weather data folder (optional)
DECADES = [(11, 20), (21, 30), (31, 40), (41, 50)]  # four blocks of ten monitored years
SHOW = [17, 21, 31, 37]  # years discussed in Section IV.E
GOOD_IS_HIGH = {"Accuracy", "F1_Score"}  # shown as scores, degraded when below the threshold


def shown(m, v):  # value in the unit of the paper
    return round(1 - v, 4) if m in GOOD_IS_HIGH else v  # accuracy and F1 as scores


res, debt_years = {}, {}  # all numbers, debt years per model
for M in ("MLP_Weather", "LR_Weather"):  # both catalog models
    s = json.load(open(os.path.join(MON, "monitor_summary_%s.json" % M)))  # monitor summary
    yrs = list(csv.DictReader(open(os.path.join(MON, "monitor_years_%s.csv" % M))))  # years 11 to 50
    val = list(csv.DictReader(open(os.path.join(MON, "monitor_validation_%s.csv" % M))))  # 5,000 resampled years
    plan, debts = s["plan"], list(s["monitoring"]["debt"])  # metric kinds and debt names
    n_deg = lambda r: int(r["n_degraded"])  # degraded metrics in one year
    has_debt = lambda r: any(r[d] == "detected" for d in debts)  # a debt was detected
    pct = lambda n: round(100.0 * n / len(val), 1)  # percent of validation years
    D = [int(r["year"]) for r in yrs if has_debt(r)]  # years with a detected debt
    debt_years[M] = set(D)  # keep for the comparison
    v = s["validation"]  # validation counts
    res[M] = {  # numbers of this model
        "train_accuracy_pct": round(100 * s["train_acc"], 1),  # training accuracy
        "trainable_parameters": s["settings"]["parameters"],  # from the ontology
        "inference_ms_per_year": round(s["inference_ms_per_year"], 2),  # measured, stored in the ontology
        "plan": plan, "inapplicable": s["inapplicable"],  # from the ontology
        "thresholds_per_run": {B: {m: shown(m, t[m][0]) for m in plan} for B, t in s["threshold_runs"].items()},  # 95th
        "thresholds_avg": {m: round(shown(m, s["thresholds"][m][0]), 4) for m in plan},  # averaged thresholds
        "severe_avg": {m: round(s["thresholds"][m][1], 4) for m in ("MMD", "KS")},  # averaged severe levels
        "validation_pct": {m: pct(v["metric_degraded"][m]) for m in plan},  # per metric, expected near 5
        "validation_any_one_pct": pct(v["any_one_metric"]),  # one or more metrics
        "validation_any_two_pct": pct(v["any_two_metrics"]),  # two or more, related or not
        "validation_debt_pct": pct(v["any_debt_detected"]), "validation_debt_n": v["any_debt_detected"],  # debt rule
        "validation_debts": v["debt"], "validation_ruled_out": v["ruled_out"],  # per debt
        "validation_severe_pct": pct(v["attribute_degraded"]["Resilience"]),  # severe shift of MMD or KS
        "years_degraded": s["monitoring"]["metric_degraded"],  # per metric, out of 40
        "years_any_one": s["monitoring"]["any_one_metric"], "years_any_two": s["monitoring"]["any_two_metrics"],  # counts
        "years_debt": len(D), "debt_years": D, "years_debts": s["monitoring"]["debt"],  # debt years
        "years_ruled_out": s["monitoring"]["ruled_out"],  # missing history
        "debt_years_accuracy_normal": sum(r["deg_Accuracy"] == "0" for r in yrs if has_debt(r)),  # accuracy saw nothing
        "one_metric_only_years": [int(r["year"]) for r in yrs if not has_debt(r) and  # complete pattern, one metric
                                  any(r[d] == "one_metric_only" for d in debts)],  # years
        "ks_only_years": [int(r["year"]) for r in yrs if n_deg(r) == 1 and r["deg_KS"] == "1"],  # KS alone
        "decade_debts": {"%d-%d" % (a, b): sum(a <= t <= b for t in D) for a, b in DECADES},  # per decade
        "mean_accuracy_pct": round(sum(100 * (1 - float(r["v_Accuracy"])) for r in yrs) / len(yrs), 1),  # 40 years
        "example_years": {r["year"]: {"values": {m: round(shown(m, float(r["v_" + m])), 4) for m in plan},  # Section IV.E
                                      "degraded": [m for m in plan if r["deg_" + m] == "1"],  # degraded metrics
                                      "attributes": [a for a in s["monitoring"]["attribute_degraded"] if r[a] == "1"],  # attributes
                                      "debts": {d: r[d] for d in debts if r[d] != "none"}, "ruled_out": r["ruled_out"]}  # debts
                          for r in yrs if int(r["year"]) in SHOW},  # chosen years
        "validation_year_3": {"values": {m: round(shown(m, float(val[2]["v_" + m])), 4) for m in plan},  # a normal resampled year
                              "degraded": [m for m in plan if val[2]["deg_" + m] == "1"]},  # its degraded metrics (none)
    }  # end of this model
res["debt_both"] = len(debt_years["MLP_Weather"] & debt_years["LR_Weather"])  # agreement between the models
res["debt_LR_only"] = sorted(debt_years["LR_Weather"] - debt_years["MLP_Weather"])  # LR only years
res["debt_MLP_only"] = sorted(debt_years["MLP_Weather"] - debt_years["LR_Weather"])  # MLP only years
if DATA:  # data statistics
    y = [int(float(v)) for v in open(os.path.join(DATA, "NEweather_class.csv"))]  # 1 = rain
    share = lambda a, b: round(100.0 * sum(y[(a - 1) * 360:b * 360]) / ((b - a + 1) * 360), 1)  # rain share of years a to b
    res["data"] = {"days": len(y), "rain_days": sum(y), "rain_pct": round(100.0 * sum(y) / len(y), 1),  # whole record
                   "rain_pct_years_1_5": share(1, 5), "rain_pct_years_41_50": share(41, 50),  # slow drift
                   "fixed_pressure_rows": json.load(open(os.path.join(MON, "monitor_summary_MLP_Weather.json")))["fixed_pressure_rows"]}  # cleaning
json.dump(res, open(OUT, "w"), indent=1)  # save
print(json.dumps(res, indent=1))  # show
