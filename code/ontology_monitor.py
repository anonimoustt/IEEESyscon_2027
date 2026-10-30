# Ontology driven monitor of one model on the NOAA weather data.
# Model settings, the ten metric kinds, metric to attribute links, debt definitions, and history checks come from the
# static ontology through the SPARQL files in queries/. The code only binds ontology names to implementations.
# Thresholds are set from resampled years of normal operation (runs of 200, 400, 800, 1600 years, then averaged),
# checked on 5,000 new resampled years, written back into the ontology, and applied to every monitored year.
# Usage: python ontology_monitor.py ONTOLOGY_IN QUERY_DIR DATA_DIR MODEL OUT_DIR ONTOLOGY_OUT
import csv  # output tables
import json  # summary
import math  # nearest rank percentile
import os  # paths
import sys  # command line arguments
import time  # inference time
from decimal import Decimal  # exact decimal text for xsd:decimal

import numpy as np  # arrays
import rdflib  # RDF graph and SPARQL
from rdflib import OWL, RDF, XSD, Literal, Namespace  # vocabularies and literals
from sklearn.linear_model import LogisticRegression  # algorithm binding
from sklearn.neural_network import MLPClassifier  # algorithm binding

ONTO_IN, QDIR, DATA, MODEL, OUT, ONTO_OUT = sys.argv[1:7]  # inputs and outputs
os.makedirs(OUT, exist_ok=True)  # output folder
C = Namespace("http://example.org/ml_core.owl#")  # core namespace
T = Namespace("http://example.org/ml_trust.owl#")  # extension namespace
g = rdflib.Graph().parse(ONTO_IN, format="xml")  # the ontology as RDF triples


def ask(name):  # run one query file for this model
    text = open(os.path.join(QDIR, name + ".rq")).read()  # query text as used in Protégé
    return list(g.query(text.replace("t:MLP_Weather", "t:" + MODEL)))  # the example model becomes the model under study


def local(v):  # local name of an IRI
    return str(v).split("#")[-1]  # text after the hash


# Step 1. Model information from the ontology
row = ask("Q2_monitoring_settings")[0]  # one row of settings
S = {k: (None if row[k] is None else row[k].toPython()) for k in row.labels}  # Python values
S = {k: (float(v) if isinstance(v, Decimal) else v) for k, v in S.items()}  # decimals as floats
S["algorithm"] = local(row["algorithm"])  # algorithm name
S["resampleSizes"] = sorted(int(v) for v in str(row["resampleSizes"]).split(","))  # 200, 400, 800, 1600
LINKS, SEVERE = {}, {}  # metric kind to attributes, direct and severe only
for r in ask("Q3_monitoring_plan"):  # applicable monitored kinds and their attributes
    m, a = local(r["metric"]), local(r["attribute"])  # names
    LINKS.setdefault(m, set()); SEVERE.setdefault(m, set())  # create entries
    (LINKS if str(r["link"]) == "direct" else SEVERE)[m].add(a)  # direct or severe link
ORDER = ["Accuracy", "F1_Score", "Accuracy_Variance", "MMD", "KS", "Unsafe_Output_Rate", "Attack_Success_Rate",  # print order
         "Prediction_Flip_Rate", "Explanation_Stability", "Explanation_Fidelity"]  # print order, continued
PLAN = [m for m in ORDER if m in LINKS]  # monitored and applicable kinds
SKIPPED = [local(r["metric"]) for r in ask("Q4_inapplicable_metrics") if local(r["model"]) == MODEL]  # not applicable
TDI, PROV = {}, {}  # debt to its attributes, debt to required history
for r in ask("Q7_debt_definitions"):  # one row per debt and attribute
    d = local(r["debt"])  # debt name
    TDI.setdefault(d, set()).add(local(r["attribute"]))  # attributes of the debt
    PROV[d] = r["provenance"]  # history class or None
HOLDS = {d: (p is None) or bool(g.query("ASK { ?m <%s> ?f . ?f a <%s> . }" % (C.has_configuration, p),  # history on record
                                          initBindings={"m": T[MODEL]}).askAnswer) for d, p in PROV.items()}  # per debt
ATTRS = ["Correctness", "Reliability", "Safety", "Security", "Resilience", "Predictability", "Transparency_Interpretability"]  # A1 to A7

# Step 2. Data: 50 years of 360 days, standardized with training statistics
DAYS = S["checkDays"]  # days per year
X_all = np.loadtxt(os.path.join(DATA, "NEweather_data.csv"), delimiter=",")  # eight features per day
y_all = np.loadtxt(os.path.join(DATA, "NEweather_class.csv"), delimiter=",").astype(int)  # 1 = rain
FIXED = [int(i) for i in np.where(X_all[:, 2] > 1100)[0]]  # impossible sea level pressure (hPa): two days in year 10
for i in FIXED: X_all[i, 2] = X_all[i - 1, 2]  # replaced by the value of the day before
n_years = len(X_all) // DAYS  # complete years
X_all, y_all = X_all[:n_years * DAYS], y_all[:n_years * DAYS]  # drop the partial year
year = np.arange(len(X_all)) // DAYS + 1  # year of each day
tr = (year >= S["trainFrom"]) & (year <= S["trainTo"])  # training years
cm = (year >= S["commFrom"]) & (year <= S["commTo"])  # normal operation years
mu, sd = X_all[tr].mean(0), X_all[tr].std(0)  # training statistics
Z_all = (X_all - mu) / sd  # standardized features
rng = np.random.default_rng(S["seed"])  # reference sample randomness

# Step 3. Algorithm binding and the model functions the metrics need
ALGORITHMS = {"Multilayer_Perceptron": lambda s: MLPClassifier(hidden_layer_sizes=(s["hiddenUnits"],),  # one hidden layer
                                                               max_iter=s["maxIter"], random_state=s["seed"]),  # settings
              "Logistic_Regression": lambda s: LogisticRegression(max_iter=s["maxIter"])}  # linear model
model = ALGORITHMS[S["algorithm"]](S)  # build the model the ontology describes
model.fit(Z_all[tr], y_all[tr])  # train once, never updated


def logit(x):  # model output before the sigmoid
    if S["algorithm"] == "Multilayer_Perceptron":  # one hidden ReLU layer
        h = np.maximum(x @ model.coefs_[0] + model.intercepts_[0], 0)  # hidden layer
        return h @ model.coefs_[1][:, 0] + model.intercepts_[1][0]  # output
    return x @ model.coef_[0] + model.intercept_[0]  # linear model


def grad(x):  # signed input gradient of the logit, one row per day
    if S["algorithm"] == "Multilayer_Perceptron":  # chain rule through the active units
        on = (x @ model.coefs_[0] + model.intercepts_[0]) > 0  # active hidden units
        return (on * model.coefs_[1][:, 0]) @ model.coefs_[0].T  # gradient
    return np.tile(model.coef_[0], (len(x), 1))  # constant for a linear model


# Step 4. Shift statistics against reference training days
N_REF = S["refSize"]  # reference size
R = Z_all[tr][rng.choice(tr.sum(), N_REF, replace=False)]  # reference training days


def sqdist(a, b):  # pairwise squared distances
    return np.maximum((a ** 2).sum(1)[:, None] + (b ** 2).sum(1)[None, :] - 2 * a @ b.T, 0)  # Euclidean


gamma = 1.0 / np.median(sqdist(R, R)[np.triu_indices(N_REF, 1)])  # median heuristic bandwidth
Krr = np.exp(-gamma * sqdist(R, R))  # reference kernel
term_rr = (Krr.sum() - np.trace(Krr)) / (N_REF * (N_REF - 1))  # reference term
R_sorted = np.sort(R, axis=0)  # reference values per feature


def mmd2(x):  # unbiased squared MMD to the reference (Gretton et al. 2012)
    Kxx = np.exp(-gamma * sqdist(x, x))  # year kernel
    n = len(x)  # days
    return (Kxx.sum() - np.trace(Kxx)) / (n * (n - 1)) + term_rr - 2 * np.exp(-gamma * sqdist(x, R)).mean()  # estimate


def ks(x):  # largest per feature KS statistic to the reference (Rabanser et al. 2019)
    xs = np.sort(x, axis=0)  # year values per feature
    best = 0.0  # running maximum
    for d in range(x.shape[1]):  # each feature
        gr = np.concatenate([R_sorted[:, d], xs[:, d]])  # all jump points
        fr = np.searchsorted(R_sorted[:, d], gr, side="right") / len(R)  # reference CDF
        fx = np.searchsorted(xs[:, d], gr, side="right") / len(x)  # year CDF
        best = max(best, np.abs(fr - fx).max())  # KS distance
    return best  # value


def f1_loss(c):  # 1 minus the F1 score of the rain class
    tp = ((c["pred"] == 1) & (c["y"] == 1)).sum(); fp = ((c["pred"] == 1) & (c["y"] == 0)).sum()  # true and false positives
    fn = ((c["pred"] == 0) & (c["y"] == 1)).sum()  # missed rain days
    return 1 - (2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 1.0)  # larger is worse


def explanation_instability(c):  # 1 minus the mean cosine of clean and noisy saliency maps
    g0, g1 = np.abs(c["g"]), np.abs(grad(c["xn"]))  # saliency of each day
    cos = (g0 * g1).sum(1) / (np.linalg.norm(g0, axis=1) * np.linalg.norm(g1, axis=1) + 1e-12)  # cosine per day
    return 1 - cos.mean()  # larger is worse


def explanation_infidelity(c):  # Yeh et al. (2019) infidelity with one feature removed at a time
    att = c["g"] * c["x"]  # gradient times input; the baseline is the training mean, 0 after standardizing
    eff = np.stack([c["z"] - logit(np.where(np.arange(c["x"].shape[1]) == i, 0.0, c["x"]))  # output change when
                    for i in range(c["x"].shape[1])], axis=1)  # feature i is set to the baseline
    return ((att - eff) ** 2).mean()  # larger is worse


METRICS = {"Accuracy": lambda c: 1 - c["hit"].mean(),  # error rate, larger is worse
           "F1_Score": f1_loss,  # rain class F1, as a loss
           "Accuracy_Variance": lambda c: np.var([c["hit"][c["y"] == k].mean() for k in (0, 1) if (c["y"] == k).any()]),  # per class
           "MMD": lambda c: mmd2(c["x"]),  # input shift
           "KS": lambda c: ks(c["x"]),  # input shift
           "Unsafe_Output_Rate": lambda c: ((c["pred"] == 0) & (c["y"] == 1)).sum() / max((c["y"] == 1).sum(), 1),  # missed rain
           "Attack_Success_Rate": lambda c: (c["pred_adv"] != c["pred"]).mean(),  # flips under a worst case change
           "Prediction_Flip_Rate": lambda c: (c["pred_n"] != c["pred"]).mean(),  # flips under random noise
           "Explanation_Stability": explanation_instability,  # saliency change under noise
           "Explanation_Fidelity": explanation_infidelity}  # saliency against real output changes


def scores(x, y, gen):  # the planned metrics for one year of 360 days
    z = logit(x); pred = (z >= 0).astype(int); gr = grad(x)  # output, prediction, gradient
    xn = x + S["sigma"] * gen.standard_normal(x.shape)  # random noise of 0.1 training standard deviations
    step = np.where(pred[:, None] == 1, -1.0, 1.0) * np.sign(gr)  # direction toward the other class
    c = {"x": x, "y": y, "z": z, "pred": pred, "hit": pred == y, "g": gr, "xn": xn,  # year context
         "pred_n": (logit(xn) >= 0).astype(int),  # predictions under noise
         "pred_adv": (logit(x + S["epsilon"] * step) >= 0).astype(int)}  # predictions under the worst case change
    return np.array([METRICS[m](c) for m in PLAN])  # one value per planned kind


# Step 5. Resampled years of normal operation: 12 random months of 30 days from the normal years
months = np.where(cm)[0].reshape(-1, S["blockDays"])  # 60 months


def resampled_year(gen):  # one resampled year
    pick = months[gen.choice(len(months), DAYS // S["blockDays"], replace=True)].ravel()  # 360 days
    return scores(Z_all[pick], y_all[pick], gen)  # metric values


def nearest_rank(v, p):  # percentile by the nearest rank method
    return np.sort(v)[math.ceil(p * len(v) / 100) - 1]  # value at that rank


runs = {}  # thresholds of each run
for B in S["resampleSizes"]:  # 200, 400, 800, 1600
    gen = np.random.default_rng([int(S["seed"]), B])  # own random stream per run
    V = np.array([resampled_year(gen) for _ in range(B)])  # B resampled years
    runs[B] = {m: (float(nearest_rank(V[:, j], S["pct"])), float(nearest_rank(V[:, j], S["pctSevere"])))  # 95th and 99th
               for j, m in enumerate(PLAN)}  # per metric
tau = np.array([np.mean([runs[B][m][0] for B in runs]) for m in PLAN])  # averaged thresholds
tau_sev = np.array([np.mean([runs[B][m][1] for B in runs]) for m in PLAN])  # averaged severe levels

# Step 6. Write thresholds and inference time into the ontology
profile = g.value(T[MODEL], T.has_commissioning_profile)  # threshold profile of this model


def dec(v):  # exact decimal literal
    return Literal(format(Decimal(repr(float(v))), "f"), datatype=XSD.decimal)  # xsd:decimal


for j, m in enumerate(PLAN):  # one Threshold_Entry per planned kind
    e = T["%s_%s_Threshold" % (MODEL, m)]  # entry IRI
    g.add((e, RDF.type, OWL.NamedIndividual)); g.add((e, RDF.type, T.Threshold_Entry))  # typed individual
    g.add((e, T.for_metric_kind, T[m])); g.add((profile, T.has_threshold_entry, e))  # kind and profile links
    g.add((e, T.has_tau, dec(tau[j]))); g.add((e, T.has_tau_sev, dec(tau_sev[j])))  # both thresholds
x_year = Z_all[year == S["commFrom"]]  # one year of inputs
t0 = time.perf_counter(); [model.predict_proba(x_year) for _ in range(200)]  # 200 timed predictions
inf_ms = (time.perf_counter() - t0) / 200 * 1000  # milliseconds per year of 360 days
g.add((T[MODEL], T.has_inference_time_ms, dec(round(inf_ms, 3))))  # stored with the model
g.serialize(ONTO_OUT, format="xml")  # the ontology with thresholds
TAU = {local(r["metric"]): (float(r["tau"]), float(r["tauSevere"])) for r in ask("Q8_thresholds")}  # read back
tau = np.array([TAU[m][0] for m in PLAN]); tau_sev = np.array([TAU[m][1] for m in PLAN])  # threshold vectors


# Step 7. Debt rule: a metric degrades its attributes; a debt needs all its attributes and two different metrics
def detect(s):  # one year
    deg, sev = s > tau, s > tau_sev  # degraded and severe metrics
    sup = {m: LINKS[m] | (SEVERE[m] if sev[j] else set()) for j, m in enumerate(PLAN) if deg[j]}  # degraded attributes per metric
    Z = set().union(*sup.values()) if sup else set()  # degraded attributes
    state, ruled_out = {}, []  # debt states and patterns without history
    for d, t in TDI.items():  # each debt
        if t <= Z and HOLDS[d]:  # all attributes degraded and history on record
            n = sum(1 for a in sup.values() if a & t)  # different metrics behind the debt
            state[d] = "detected" if n >= 2 else "one_metric_only"  # two or more metrics detect it
        else:  # not complete
            state[d] = "none"  # no debt
            if t <= Z: ruled_out.append(d)  # complete pattern, missing history
    return deg, Z, state, ruled_out  # results


def row_of(label, s):  # one output row
    deg, Z, st, ro = detect(s)  # decisions
    return ([label] + [float(v) for v in s] + [int(v) for v in deg] + [int(a in Z) for a in ATTRS] +  # values and flags
            [int(deg.sum())] + [st[d] for d in sorted(TDI)] + [";".join(sorted(ro))])  # count, debts, ruled out


# Step 8. Validation on 5,000 new resampled years, then the monitored years 11 to 50
val_gen = np.random.default_rng([int(S["seed"]), 1])  # independent stream for validation
val = [row_of(i + 1, resampled_year(val_gen)) for i in range(S["validationYears"])]  # 5,000 resampled years
mon_gen = np.random.default_rng([int(S["seed"]), 2])  # noise stream for the monitored years
rows = [row_of(t, scores(Z_all[year == t], y_all[year == t], mon_gen)) for t in range(S["opFrom"], S["opTo"] + 1)]  # yearly
cols = (["year"] + ["v_" + m for m in PLAN] + ["deg_" + m for m in PLAN] + ATTRS + ["n_degraded"] +  # columns
        sorted(TDI) + ["ruled_out"])  # columns, continued
for name, rr in (("monitor_years_%s.csv" % MODEL, rows), ("monitor_validation_%s.csv" % MODEL, val)):  # save both
    with open(os.path.join(OUT, name), "w", newline="") as f:  # file
        w = csv.writer(f); w.writerow(cols); w.writerows(rr)  # header and rows


def rates(rr):  # counts over a set of years
    k = len(PLAN)  # number of metrics
    return {"years": len(rr),  # count
            "metric_degraded": {m: sum(r[1 + k + j] for r in rr) for j, m in enumerate(PLAN)},  # per metric
            "any_one_metric": sum(r[1 + 2 * k + len(ATTRS)] >= 1 for r in rr),  # one or more metrics degraded
            "any_two_metrics": sum(r[1 + 2 * k + len(ATTRS)] >= 2 for r in rr),  # two or more, related or not
            "attribute_degraded": {a: sum(r[1 + 2 * k + i] for r in rr) for i, a in enumerate(ATTRS)},  # per attribute
            "debt": {d: {s: sum(r[cols.index(d)] == s for r in rr) for s in ("detected", "one_metric_only")}  # per debt
                     for d in sorted(TDI)},  # every debt
            "any_debt_detected": sum(any(r[cols.index(d)] == "detected" for d in TDI) for r in rr),  # some debt detected
            "ruled_out": {d: sum(d in r[-1].split(";") for r in rr) for d in sorted(TDI)}}  # missing history


summary = {"model": MODEL, "settings": S, "fixed_pressure_rows": FIXED, "plan": PLAN, "inapplicable": SKIPPED, "history_holds": HOLDS,  # from the ontology
           "train_acc": float(model.score(Z_all[tr], y_all[tr])), "inference_ms_per_year": inf_ms,  # fit and speed
           "threshold_runs": {str(B): runs[B] for B in runs}, "thresholds": TAU,  # per run and averaged
           "validation": rates(val), "monitoring": rates(rows)}  # counts
json.dump(summary, open(os.path.join(OUT, "monitor_summary_%s.json" % MODEL), "w"), indent=1, default=str)  # save
print(json.dumps({"model": MODEL, "plan": PLAN, "inapplicable": SKIPPED, "inference_ms": round(inf_ms, 3)}))  # report
print(json.dumps({k: {q: summary[k][q] for q in ("any_one_metric", "any_two_metrics", "any_debt_detected")}  # report
                  for k in ("validation", "monitoring")}))  # report
