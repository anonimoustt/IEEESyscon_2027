# Figure of the 40 monitored years of MLP_Weather and LR_Weather, from metrics to attributes to debts (repository only).
# Hatching comes from the ontology: Q4 (metrics that do not apply), Q5 (blind spots), and Q6 (detectable debts).
# Usage: python fig_weather.py MONITOR_DIR QUERY_RESULTS_DIR OUT_PDF
import csv  # read the checks and query results
import json  # read the thresholds
import os  # paths
import sys  # command line arguments

import matplotlib  # plotting
matplotlib.use("Agg")  # no display
import matplotlib.pyplot as plt  # figure
from matplotlib.patches import Patch, Rectangle  # cells and legend
from matplotlib.lines import Line2D  # legend marker
import numpy as np  # arrays

MON, QRES, OUT = sys.argv[1:4]  # inputs and output
plt.rcParams.update({"font.size": 7, "hatch.linewidth": 0.5})  # readable at print size
KINDS = ["Accuracy", "F1_Score", "Accuracy_Variance", "MMD", "KS", "Unsafe_Output_Rate", "Attack_Success_Rate",  # metric rows
         "Prediction_Flip_Rate", "Explanation_Stability", "Explanation_Fidelity"]  # metric rows, continued
LAB_M = ["Accuracy", "F1 score", "Accuracy variance", "MMD", "KS", "Unsafe output rate", "Attack success rate",  # labels
         "Flip rate", "Explanation stability", "Explanation fidelity"]  # labels, continued
NM, NA = len(KINDS), 7  # metric and attribute rows
ATTRS = ["Correctness", "Reliability", "Safety", "Security", "Resilience", "Predictability", "Transparency_Interpretability"]  # rows
LAB_A = ["Correctness", "Reliability", "Safety", "Security", "Resilience", "Predictability", "Transparency"]  # labels
DEBTS = ["Source_Target_Mismatch", "Capability_Loss", "Robustness_Debt", "Operating_Envelope", "Harmful_Output", "Faithfulness"]  # rows
LAB_D = ["Source Target Mismatch", "Capability Loss", "Robustness", "Operating Envelope", "Harmful Output", "Faithfulness"]  # labels
q = lambda n: list(csv.DictReader(open(os.path.join(QRES, n + ".csv"))))  # query result rows
INAPP = {(r["model"], r["metric"]) for r in q("Q4_inapplicable_metrics")}  # gated metric kinds
BLIND = {(r["model"], r["attribute"]) for r in q("Q5_blind_spots")}  # attributes without a metric
DETECT = {(r["model"], r["debt"]) for r in q("Q6_detectable_debts")}  # detectable debts
ROWS = [(k, "m") for k in KINDS] + [(a, "a") for a in ATTRS] + [(d, "d") for d in DEBTS]  # all rows
YPOS, y = [], 0.0  # top of each row
for i, _ in enumerate(ROWS):  # place rows
    if i in (NM, NM + NA):  # new layer
        y += 0.8  # gap
    YPOS.append(y); y += 1  # row top and height
YMAX = y  # grid height

def panel(a_top, a_grid, model, title, first):  # accuracy strip and grid of one model
    rows = list(csv.DictReader(open(os.path.join(MON, "monitor_years_%s.csv" % model))))  # monitored years
    tau = json.load(open(os.path.join(MON, "monitor_summary_%s.json" % model)))["thresholds"]["Accuracy"][0]  # error threshold
    acc = [100 * (1 - float(r["v_Accuracy"])) for r in rows]  # accuracy per year
    a_top.plot(np.arange(len(rows)) + 0.5, acc, color="black", lw=0.9, marker="o", ms=1.6)  # accuracy line
    a_top.axhline(100 * (1 - tau), color="0.45", lw=0.8, ls=":")  # degraded below this line
    a_top.set_xlim(0, len(rows)); a_top.set_ylim(64, 87); a_top.set_yticks([66, 76, 86]); a_top.set_xticks([])  # axes
    a_top.set_title(title, fontsize=7.5, pad=3)  # panel title
    for side in ("top", "right"):  # open frame
        a_top.spines[side].set_visible(False)  # hide
    for (key, kind), y0 in zip(ROWS, YPOS):  # each row
        gated = ((kind == "m" and ((model, key) in INAPP or key not in [c[2:] for c in rows[0] if c.startswith("v_")]))  # no metric
                 or (kind == "a" and (model, key) in BLIND) or (kind == "d" and (model, key) not in DETECT))  # blind or undetectable
        for c, r in enumerate(rows):  # each year
            face, hatch = "white", None  # default: healthy or inactive
            if gated:  # nothing can be observed here
                hatch = "////"  # hatched
            elif kind == "m" and r["deg_" + key] == "1":  # degraded metric
                face = "black"  # black
            elif kind == "a" and r[key] == "1":  # degraded attribute
                face = "black"  # black
            elif kind == "d":  # debt state
                face = {"detected": "black", "one_metric_only": "0.6"}.get(r[key], "white")  # state shade
            a_grid.add_patch(Rectangle((c, y0), 1, 1, facecolor=face, edgecolor="0.8", lw=0.3, hatch=hatch))  # cell
            if kind == "d" and key in r["ruled_out"].split(";"):  # complete pattern, no history on record
                a_grid.plot(c + 0.5, y0 + 0.5, marker="x", ms=2.6, mew=0.6, color="black")  # cross
    a_grid.set_xlim(0, len(rows)); a_grid.set_ylim(YMAX, 0)  # grid extent
    ticks = [0, 9, 19, 29, len(rows) - 1]  # years 11, 20, 30, 40, 50
    a_grid.set_xticks([t + 0.5 for t in ticks]); a_grid.set_xticklabels([rows[t]["year"] for t in ticks])  # years
    a_grid.set_xlabel("Year (360 days)", labelpad=1)  # x label
    a_grid.tick_params(axis="y", length=0)  # no tick marks
    for s_ in a_grid.spines.values():  # frame
        s_.set_visible(False)  # none
    if first:  # labels on the left panel only
        a_top.set_ylabel("Accuracy (%)", fontsize=6.5, labelpad=2)  # y label
        a_grid.set_yticks([y0 + 0.5 for y0 in YPOS]); a_grid.set_yticklabels(LAB_M + LAB_A + LAB_D)  # row labels
        for name, i0, i1 in (("Raw metrics", 0, NM - 1), ("Attributes", NM, NM + NA - 1), ("Debts", NM + NA, NM + NA + 5)):  # layers
            yc = (YPOS[i0] + YPOS[i1] + 1) / 2  # layer centre
            a_grid.text(-0.465, yc, name, rotation=90, ha="center", va="center", fontsize=7, fontweight="bold",  # label
                        clip_on=False, transform=a_grid.get_yaxis_transform())  # x in panel widths
            a_grid.plot([-0.44, -0.44], [YPOS[i0] + 0.1, YPOS[i1] + 0.9], color="black", lw=0.6, clip_on=False,  # bracket
                        transform=a_grid.get_yaxis_transform())  # x in panel widths
    else:  # right panel
        a_grid.set_yticks([]); a_top.set_yticklabels([])  # no repeated labels

fig = plt.figure(figsize=(7.0, 3.9))  # full text width
gs = fig.add_gridspec(2, 2, height_ratios=[1, 5.6], hspace=0.06, wspace=0.05, left=0.205, right=0.995, top=0.945, bottom=0.165)  # layout
panel(fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[1, 0]), "MLP_Weather", "(a) MLP_Weather (neural network)", True)  # left
panel(fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 1]), "LR_Weather", "(b) LR_Weather (logistic regression)", False)  # right
fig.legend(handles=[Patch(facecolor="black", label="degraded metric or attribute; detected debt"),  # legend entry
                    Patch(facecolor="0.6", label="all attributes degraded, but by one metric only"),  # legend entry
                    Line2D([], [], marker="x", ls="none", color="black", ms=3.5, label="ruled out: no fine tuning or transfer"),  # entry
                    Patch(facecolor="white", edgecolor="0.6", hatch="////", label="no metric, inapplicable, or undetectable")],  # entry
           loc="lower center", ncol=2, frameon=False, fontsize=6.3, bbox_to_anchor=(0.6, -0.015), handlelength=1.3,  # placement
           columnspacing=1.0)  # compact
fig.savefig(OUT)  # vector figure for the paper
fig.savefig(OUT.replace(".pdf", ".png"), dpi=220)  # preview image
