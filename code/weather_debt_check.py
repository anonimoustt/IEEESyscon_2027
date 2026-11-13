# Independent check of ontology_monitor.py. It does not read the ontology: settings and links are typed in from
# Tables I and II, and the metrics use library routines where possible (scipy KS, sklearn F1 and recall).
# It recomputes thresholds, the 5,000 validation years, and years 11 to 50, then compares with the monitor files.
# Usage: python weather_debt_check.py DATA_DIR MONITOR_DIR MODEL [OUT_JSON]      (MODEL: MLP_Weather or LR_Weather)
import csv  # monitor files
import json  # monitor summary
import os  # paths
import sys  # arguments

import numpy as np  # arrays
from scipy.spatial.distance import cdist, pdist  # pairwise distances
from scipy.special import logit as inv_sigmoid  # log odds from probabilities
from scipy.stats import ks_2samp  # two sample KS test
from sklearn.linear_model import LogisticRegression  # linear model
from sklearn.metrics import f1_score, recall_score  # F1 and per class recall
from sklearn.neural_network import MLPClassifier  # network

DATA, MON, MODEL = sys.argv[1:4]  # inputs
OUT = sys.argv[4] if len(sys.argv) > 4 else None  # optional report file
SEED, DAYS, MONTH, N_REF, SIGMA, EPS = 0, 360, 30, 1000, 0.1, 0.1  # settings of Section IV
SIZES, N_VAL, PCT, PCT_SEV = (200, 400, 800, 1600), 5000, 95, 99  # threshold runs and validation
LINKS = {"Accuracy": {"C"}, "F1_Score": {"C"}, "Accuracy_Variance": {"C", "R"}, "MMD": {"R"}, "KS": {"R"},  # Table I
         "Unsafe_Output_Rate": {"S"}, "Attack_Success_Rate": {"Sec"}, "Prediction_Flip_Rate": {"P"},  # Table I
         "Explanation_Stability": {"P", "T"}, "Explanation_Fidelity": {"T"}}  # Table I
SEVERE = {"MMD", "KS"}  # also Resilience when severe
DEBTS = {"Source_Target_Mismatch": {"R", "P", "T"}, "Capability_Loss": {"C", "R"}, "Robustness_Debt": {"C", "Sec"},  # Table II
         "Operating_Envelope": {"R", "Res"}, "Harmful_Output": {"S", "Sec"}, "Faithfulness": {"P", "T"}}  # Table II
NEEDS_HISTORY = {"Source_Target_Mismatch", "Capability_Loss"}  # transfer or fine tuning on record; neither model has it
PLAN = list(LINKS) if MODEL == "MLP_Weather" else list(LINKS)[:8]  # no saliency metrics for the linear model

X = np.loadtxt(os.path.join(DATA, "NEweather_data.csv"), delimiter=",")[:50 * DAYS]  # 50 years of features
bad = np.flatnonzero(X[:, 2] > 1100)  # impossible sea level pressure
assert bad.tolist() == [3595, 3596], bad  # the two known days of year 10
X[bad, 2] = X[bad[0] - 1, 2]  # both get the last valid value
y = np.loadtxt(os.path.join(DATA, "NEweather_class.csv"), delimiter=",").astype(int)[:50 * DAYS]  # labels
yr = np.arange(len(X)) // DAYS + 1  # year of each day
tr, nm = yr <= 5, (yr >= 6) & (yr <= 10)  # training and normal years
Z = (X - X[tr].mean(0)) / X[tr].std(0)  # standardized with training statistics
if MODEL == "MLP_Weather":  # the network
    clf = MLPClassifier(hidden_layer_sizes=(16,), max_iter=3000, random_state=SEED).fit(Z[tr], y[tr])  # train
else:  # logistic regression
    clf = LogisticRegression(max_iter=2000).fit(Z[tr], y[tr])  # train


def out(x):  # log odds from the library probabilities
    p = clf.predict_proba(x)[:, 1]  # rain probability
    assert p.min() > 0 and p.max() < 1, "probability at 0 or 1"  # log odds would be lost
    return inv_sigmoid(p)  # inverse sigmoid


def grad(x):  # analytic input gradient of the log odds
    if MODEL == "LR_Weather":  # linear model
        return np.repeat(clf.coef_, len(x), axis=0)  # same for every day
    W1, b1, w2 = clf.coefs_[0], clf.intercepts_[0], clf.coefs_[1][:, 0]  # network weights
    return np.einsum("nh,dh->nd", (x @ W1 + b1 > 0) * w2, W1)  # sum over active hidden units


probe = Z[tr][:50]  # gradient test points
fd = np.stack([(out(probe + 1e-5 * e) - out(probe - 1e-5 * e)) / 2e-5 for e in np.eye(8)], axis=1)  # central differences
assert np.abs(fd - grad(probe)).max() < 1e-4, "gradient does not match finite differences"  # sanity test

rng = np.random.default_rng(SEED)  # reference sample
R = Z[tr][rng.choice(tr.sum(), N_REF, replace=False)]  # 1,000 training days
gam = 1.0 / np.median(pdist(R, "sqeuclidean"))  # median heuristic


def mmd2(x):  # unbiased squared MMD
    kxx, krr, kxr = (np.exp(-gam * cdist(a, b, "sqeuclidean")) for a, b in ((x, x), (R, R), (x, R)))  # kernels
    n, m = len(x), len(R)  # sizes
    return (kxx.sum() - n) / (n * (n - 1)) + (krr.sum() - m) / (m * (m - 1)) - 2 * kxr.mean()  # diagonal is 1


def metrics(x, t, gen):  # the planned metrics, larger is worse
    p = clf.predict(x)  # predictions
    xn = x + SIGMA * gen.standard_normal(x.shape)  # noisy copy, same draw order as the monitor
    xa = x + EPS * np.sign(grad(x)) * np.where(p == 1, -1.0, 1.0)[:, None]  # step toward the other class
    rec = recall_score(t, p, labels=[0, 1], average=None, zero_division=0)  # accuracy on dry and on rain days
    g0, g1 = np.abs(grad(x)), np.abs(grad(xn))  # saliency maps
    cos = np.sum(g0 * g1, 1) / (np.linalg.norm(g0, axis=1) * np.linalg.norm(g1, axis=1) + 1e-12)  # cosine per day
    v = {"Accuracy": np.mean(p != t),  # error rate
         "F1_Score": 1 - f1_score(t, p, pos_label=1, zero_division=1.0),  # rain F1 as a loss
         "Accuracy_Variance": ((rec[0] - rec[1]) / 2) ** 2,  # variance of two values
         "MMD": mmd2(x), "KS": max(ks_2samp(R[:, d], x[:, d]).statistic for d in range(8)),  # input shift
         "Unsafe_Output_Rate": 1 - rec[1],  # rain days predicted dry
         "Attack_Success_Rate": np.mean(clf.predict(xa) != p),  # flips under the worst case step
         "Prediction_Flip_Rate": np.mean(clf.predict(xn) != p)}  # flips under noise
    if MODEL == "MLP_Weather":  # saliency metrics
        v["Explanation_Stability"] = 1 - cos.mean()  # saliency change
        base, att = out(x), grad(x) * x  # output and gradient times input
        err = [(att[:, i] - (base - out(np.where(np.arange(8) == i, 0.0, x)))) ** 2 for i in range(8)]  # per feature
        v["Explanation_Fidelity"] = np.mean(err)  # infidelity
    return np.array([v[m] for m in PLAN])  # fixed order


blocks = np.where(nm)[0].reshape(-1, MONTH)  # 60 months of normal operation


def resampled(gen):  # one resampled year
    d = blocks[gen.choice(len(blocks), DAYS // MONTH, replace=True)].ravel()  # 12 months
    return metrics(Z[d], y[d], gen)  # its metrics


runs = {}  # thresholds per run
for B in SIZES:  # four runs
    gen = np.random.default_rng([SEED, B])  # same stream as the monitor
    V = np.array([resampled(gen) for _ in range(B)])  # B years
    runs[B] = np.quantile(V, [PCT / 100, PCT_SEV / 100], axis=0, method="inverted_cdf")  # nearest rank
tau, sev = np.mean([runs[B][0] for B in SIZES], 0), np.mean([runs[B][1] for B in SIZES], 0)  # averages


def decide(v):  # debt rule
    deg = v > tau  # step 1: degraded metrics
    ev = {m: LINKS[m] | ({"Res"} if m in SEVERE and v[j] > sev[j] else set()) for j, m in enumerate(PLAN) if deg[j]}  # step 2
    att = set().union(*ev.values()) if ev else set()  # degraded attributes
    res = {}  # step 3
    for d, need in DEBTS.items():  # each debt
        ok = need <= att and d not in NEEDS_HISTORY  # complete and possible
        res[d] = "none" if not ok else "detected" if sum(bool(a & need) for a in ev.values()) >= 2 else "one_metric_only"  # outcome
    return deg, res  # decisions


summ = json.load(open(os.path.join(MON, "monitor_summary_%s.json" % MODEL)))  # monitor summary
for B in SIZES:  # per run thresholds
    mon = np.array([summ["threshold_runs"][str(B)][m] for m in PLAN]).T  # monitor values
    assert np.allclose(mon, runs[B], rtol=1e-6, atol=1e-12), "thresholds differ for %d" % B  # same
gen_val, gen_mon = np.random.default_rng([SEED, 1]), np.random.default_rng([SEED, 2])  # same streams
checks = {"validation": [resampled(gen_val) for _ in range(N_VAL)],  # 5,000 years
          "years": [metrics(Z[yr == t], y[yr == t], gen_mon) for t in range(11, 51)]}  # monitored years
worst, wrong = 0.0, 0  # largest value gap, decision mismatches
for name, vals in checks.items():  # both sets
    rows = list(csv.DictReader(open(os.path.join(MON, "monitor_%s_%s.csv" % (name, MODEL)))))  # monitor rows
    for v, r in zip(vals, rows):  # row by row
        mv = np.array([float(r["v_" + m]) for m in PLAN])  # monitor values
        worst = max(worst, float(np.max(np.abs(mv - v) / (np.abs(v) + 1e-9))))  # relative gap
        deg, res = decide(v)  # this implementation
        wrong += any(int(r["deg_" + m]) != int(deg[j]) for j, m in enumerate(PLAN))  # metric decisions
        wrong += any(r[d] != res[d] for d in DEBTS)  # debt decisions
report = {"model": MODEL, "largest_relative_gap": worst, "decision_mismatches": wrong,  # agreement
          "years_compared": N_VAL + 40, "values_compared": (N_VAL + 40) * len(PLAN)}  # sizes
print(json.dumps(report))  # show
if OUT: json.dump(report, open(OUT, "w"), indent=1)  # save
assert wrong == 0, "the two implementations disagree"  # stop on any mismatch
