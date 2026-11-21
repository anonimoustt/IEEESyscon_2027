# Test of other splits (an extra check, not reported in the paper): repeats the experiment with other training, normal, and monitored years.
# The method is that of ontology_monitor.py; only the year sets below change. The first split is the one of the paper.
# Usage: python code/split_sensitivity.py [DATA_CSV [OUT_JSON [CONFIG ...]]]   (defaults: the joined data file, results/split_sensitivity.json)
import json  # results file
import os  # paths
import sys  # arguments
from multiprocessing import Pool  # two runs at a time

import numpy as np  # arrays
from sklearn.linear_model import LogisticRegression  # linear model
from sklearn.neural_network import MLPClassifier  # network

SEED, DAYS, MONTH, N_REF, SIGMA, EPS = 0, 360, 30, 1000, 0.1, 0.1  # settings of Section IV
SIZES, N_VAL, PCT, PCT_SEV = (200, 400, 800, 1600), 5000, 95, 99  # threshold runs and validation
LINKS = {"Accuracy": {"C"}, "F1_Score": {"C"}, "Accuracy_Variance": {"C", "R"}, "MMD": {"R"}, "KS": {"R"},  # Table I
         "Unsafe_Output_Rate": {"S"}, "Attack_Success_Rate": {"Sec"}, "Prediction_Flip_Rate": {"P"},  # Table I
         "Explanation_Stability": {"P", "T"}, "Explanation_Fidelity": {"T"}}  # Table I
SEVERE = {"MMD", "KS"}  # also Resilience when severe
DEBTS = {"Source_Target_Mismatch": {"R", "P", "T"}, "Capability_Loss": {"C", "R"}, "Robustness_Debt": {"C", "Sec"},  # Table II
         "Operating_Envelope": {"R", "Res"}, "Harmful_Output": {"S", "Sec"}, "Faithfulness": {"P", "T"}}  # Table II
NEEDS_HISTORY = {"Source_Target_Mismatch", "Capability_Loss"}  # neither model has this history


def years(a, b):  # inclusive range of years
    return list(range(a, b + 1))  # list


def random_split(seed):  # five training and five normal years picked at random, the other 40 monitored
    p = np.random.default_rng(1000 + seed).permutation(np.arange(1, 51))  # shuffled years
    return sorted(p[:5].tolist()), sorted(p[5:10].tolist()), sorted(p[10:].tolist())  # three sets


CONFIGS = {"paper_train_1_5": (years(1, 5), years(6, 10), years(11, 50)),  # split of the paper
           "train_1_10": (years(1, 10), years(11, 15), years(16, 50)),  # ten training years
           "normal_25_30": (years(1, 5), years(25, 30), years(11, 50)),  # thresholds from late years
           **{"random_%d" % s: random_split(s) for s in range(1, 6)}}  # five random splits


def load(path):  # features and labels of the first 50 years
    raw = np.loadtxt(path, delimiter=",", skiprows=1)[:50 * DAYS]  # day, year, eight features, rain
    X, y = raw[:, 2:10].copy(), raw[:, 10].astype(int)  # features and label
    bad = np.flatnonzero(X[:, 2] > 1100)  # impossible sea level pressure
    assert bad.tolist() == [3595, 3596], bad  # the two known days of year 10
    X[bad, 2] = X[bad[0] - 1, 2]  # both get the last valid value
    return X, y  # arrays


def run(job):  # one model on one split
    path, name, model = job  # inputs
    train, normal, monitor = CONFIGS[name]  # year sets
    X, y = load(path)  # data
    yr = np.arange(len(X)) // DAYS + 1  # year of each day
    tr, nm = np.isin(yr, train), np.isin(yr, normal)  # training and normal days
    Z = (X - X[tr].mean(0)) / X[tr].std(0)  # standardized with training statistics
    plan = list(LINKS) if model == "MLP_Weather" else list(LINKS)[:8]  # no saliency metrics for the linear model
    if model == "MLP_Weather":  # the network
        clf = MLPClassifier(hidden_layer_sizes=(16,), max_iter=3000, random_state=SEED).fit(Z[tr], y[tr])  # train
        W1, b1, w2, b2 = clf.coefs_[0], clf.intercepts_[0], clf.coefs_[1][:, 0], clf.intercepts_[1][0]  # weights
        logit = lambda x: np.maximum(x @ W1 + b1, 0) @ w2 + b2  # output before the sigmoid
        grad = lambda x: ((x @ W1 + b1 > 0) * w2) @ W1.T  # input gradient
    else:  # logistic regression
        clf = LogisticRegression(max_iter=2000).fit(Z[tr], y[tr])  # train
        logit = lambda x: x @ clf.coef_[0] + clf.intercept_[0]  # linear output
        grad = lambda x: np.tile(clf.coef_[0], (len(x), 1))  # constant gradient
    rng = np.random.default_rng(SEED)  # reference sample
    R = Z[tr][rng.choice(tr.sum(), N_REF, replace=False)]  # 1,000 training days
    sq = lambda a, b: np.maximum((a ** 2).sum(1)[:, None] + (b ** 2).sum(1)[None, :] - 2 * a @ b.T, 0)  # squared distances
    gam = 1.0 / np.median(sq(R, R)[np.triu_indices(N_REF, 1)])  # median heuristic
    Krr = np.exp(-gam * sq(R, R)); term_rr = (Krr.sum() - np.trace(Krr)) / (N_REF * (N_REF - 1))  # reference term
    Rs = np.sort(R, axis=0)  # sorted reference values

    def mmd2(x):  # unbiased squared MMD to the reference
        Kxx = np.exp(-gam * sq(x, x)); n = len(x)  # year kernel
        return (Kxx.sum() - np.trace(Kxx)) / (n * (n - 1)) + term_rr - 2 * np.exp(-gam * sq(x, R)).mean()  # estimate

    def ks(x):  # largest per feature KS statistic to the reference
        xs, best = np.sort(x, axis=0), 0.0  # sorted year values
        for d in range(x.shape[1]):  # each feature
            gr = np.concatenate([Rs[:, d], xs[:, d]])  # jump points
            best = max(best, np.abs(np.searchsorted(Rs[:, d], gr, side="right") / len(R)  # reference CDF
                                    - np.searchsorted(xs[:, d], gr, side="right") / len(x)).max())  # year CDF
        return best  # value

    def metrics(x, t, gen):  # planned metrics of one year, larger is worse
        z = logit(x); p = (z >= 0).astype(int); g = grad(x); hit = p == t  # output, prediction, gradient
        xn = x + SIGMA * gen.standard_normal(x.shape)  # noisy copy
        pa = (logit(x + EPS * np.where(p[:, None] == 1, -1.0, 1.0) * np.sign(g)) >= 0).astype(int)  # worst case step
        tp, fp, fn = ((p == 1) & (t == 1)).sum(), ((p == 1) & (t == 0)).sum(), ((p == 0) & (t == 1)).sum()  # counts
        v = {"Accuracy": 1 - hit.mean(),  # error rate
             "F1_Score": 1 - (2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 1.0),  # rain F1 as a loss
             "Accuracy_Variance": np.var([hit[t == k].mean() for k in (0, 1) if (t == k).any()]),  # per class
             "MMD": mmd2(x), "KS": ks(x),  # input shift
             "Unsafe_Output_Rate": fn / max((t == 1).sum(), 1),  # missed rain
             "Attack_Success_Rate": (pa != p).mean(),  # flips under the worst case step
             "Prediction_Flip_Rate": ((logit(xn) >= 0).astype(int) != p).mean()}  # flips under noise
        if model == "MLP_Weather":  # saliency metrics
            g0, g1 = np.abs(g), np.abs(grad(xn))  # saliency maps
            v["Explanation_Stability"] = 1 - ((g0 * g1).sum(1) / (np.linalg.norm(g0, axis=1) * np.linalg.norm(g1, axis=1) + 1e-12)).mean()  # change
            eff = np.stack([z - logit(np.where(np.arange(8) == i, 0.0, x)) for i in range(8)], axis=1)  # effect of each feature
            v["Explanation_Fidelity"] = ((g * x - eff) ** 2).mean()  # infidelity
        return np.array([v[m] for m in plan])  # fixed order

    blocks = np.where(nm)[0].reshape(-1, MONTH)  # months of normal operation
    resampled = lambda gen: (lambda d: metrics(Z[d], y[d], gen))(blocks[gen.choice(len(blocks), DAYS // MONTH, replace=True)].ravel())  # one year
    rank = lambda v, p: np.sort(v, axis=0)[int(np.ceil(p * len(v) / 100)) - 1]  # nearest rank percentile
    th = []  # thresholds of each run
    for B in SIZES:  # four runs
        gen = np.random.default_rng([SEED, B])  # same stream as the monitor
        V = np.array([resampled(gen) for _ in range(B)])  # B resampled years
        th.append((rank(V, PCT), rank(V, PCT_SEV)))  # 95th and 99th
    tau, sev = np.mean([a for a, _ in th], 0), np.mean([b for _, b in th], 0)  # averages

    def decide(v):  # debt rule
        deg = v > tau  # degraded metrics
        ev = {m: LINKS[m] | ({"Res"} if m in SEVERE and v[j] > sev[j] else set()) for j, m in enumerate(plan) if deg[j]}  # attributes
        att = set().union(*ev.values()) if ev else set()  # degraded attributes
        det = [d for d, need in DEBTS.items() if need <= att and d not in NEEDS_HISTORY  # complete and possible
               and sum(bool(a & need) for a in ev.values()) >= 2]  # two or more metrics
        return deg, det  # decisions

    gv, gm = np.random.default_rng([SEED, 1]), np.random.default_rng([SEED, 2])  # validation and monitoring streams
    val = [decide(resampled(gv)) for _ in range(N_VAL)]  # 5,000 validation years
    mon = {t: decide(metrics(Z[yr == t], y[yr == t], gm)) for t in monitor}  # monitored years
    ia, ik = plan.index("Accuracy"), plan.index("KS")  # positions
    debt_years = [t for t in monitor if mon[t][1]]  # years with a debt
    per = np.mean([d for d, _ in val], 0) * 100  # per metric rate in validation
    return {"config": name, "model": model, "train": train, "normal": normal, "n_monitor": len(monitor),  # split
            "train_acc_pct": round(100 * clf.score(Z[tr], y[tr]), 1),  # fit
            "acc_threshold_pct": round(100 * (1 - tau[ia]), 1), "ks_threshold": round(float(tau[ik]), 3),  # two thresholds
            "val_any_one_pct": round(100 * np.mean([d.any() for d, _ in val]), 1),  # monitor on any single metric
            "val_any_two_pct": round(100 * np.mean([d.sum() >= 2 for d, _ in val]), 1),  # any two metrics
            "val_debt_pct": round(100 * np.mean([bool(x) for _, x in val]), 1),  # debt rule
            "val_per_metric_pct": [round(float(per.min()), 1), round(float(per.max()), 1)],  # range over metrics
            "debt_years": debt_years, "n_debt_years": len(debt_years),  # monitored years with a debt
            "debt_years_acc_normal": sum(1 for t in debt_years if not mon[t][0][ia]),  # accuracy above its threshold
            "ks_years": sum(1 for t in monitor if mon[t][0][ik]),  # KS over its threshold
            "acc_low_years": sum(1 for t in monitor if mon[t][0][ia]),  # accuracy below its threshold
            "debts": {d: sum(1 for t in monitor if d in mon[t][1]) for d in DEBTS}}  # count per debt


if __name__ == "__main__":  # command line
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repository folder
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "data", "noaa_weather_offutt_1949_1999.csv")  # data file
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "results", "split_sensitivity.json")  # results file
    names = sys.argv[3:] or list(CONFIGS)  # chosen splits
    jobs = [(path, n, m) for n in names for m in ("MLP_Weather", "LR_Weather")]  # every model on every split
    with Pool(2) as pool:  # two at a time
        res = pool.map(run, jobs, chunksize=1)  # run
    json.dump(res, open(out, "w"), indent=1)  # save
    print("%-16s %-12s %8s %8s %8s %6s %10s" % ("split", "model", "one %", "two %", "debt %", "debts", "acc normal"))  # header
    for r in res:  # one line per run
        print("%-16s %-12s %8.1f %8.1f %8.1f %6d %10d" % (r["config"], r["model"], r["val_any_one_pct"], r["val_any_two_pct"],  # false alarm rates
                                                        r["val_debt_pct"], r["n_debt_years"], r["debt_years_acc_normal"]))  # debt years
