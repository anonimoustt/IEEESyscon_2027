# Draws Fig. 4 (KS over time) and Fig. 5 (accuracy over time) of the paper from the monitor results of MLP_Weather.
# Usage: python code/time_figures.py results/monitor results/figures
import csv, json, sys, matplotlib
import matplotlib.ticker
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
MON, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)  # create the output folder if needed
fams = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams.update({'font.family': 'FreeSerif' if 'FreeSerif' in fams else 'DejaVu Serif', 'font.size': 8,
                     'axes.linewidth': 0.6, 'pdf.fonttype': 42})
rows = list(csv.DictReader(open(MON + '/monitor_years_MLP_Weather.csv')))
th = json.load(open(MON + '/monitor_summary_MLP_Weather.json'))['thresholds']
D = ['Capability_Loss', 'Faithfulness', 'Harmful_Output', 'Operating_Envelope', 'Robustness_Debt', 'Source_Target_Mismatch']
Y = [int(r['year']) for r in rows]
debt = [any(r[d] == 'detected' for d in D) for r in rows]
def axes(ylabel):
    fig, ax = plt.subplots(figsize=(3.45, 2.0))
    ax.set_xlim(10, 51); ax.set_xticks([11, 15, 20, 25, 30, 35, 40, 45, 50]); ax.set_xlabel('Monitored year'); ax.set_ylabel(ylabel)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.tick_params(width=0.6, length=2.5)
    return fig, ax
def finish(fig, ax, name):
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=6.5, frameon=False,
              handletextpad=0.2, columnspacing=0.8, borderaxespad=0.2)
    fig.tight_layout(pad=0.2); fig.savefig(OUT + '/' + name + '.pdf'); fig.savefig(OUT + '/' + name + '.png', dpi=200)
# Fig. 4: KS alone
ks = [float(r['v_KS']) for r in rows]; ksd = [r['deg_KS'] == '1' for r in rows]
fig, ax = axes('KS')
ax.plot(Y, ks, color='0.75', lw=0.8, zorder=1)
t, sv = th['KS']
ax.axhline(t, color='black', lw=0.8, zorder=0); ax.axhline(sv, color='0.45', lw=0.8, ls=(0, (1, 1.5)), zorder=0)
ax.text(10.3, t - 0.006, 'threshold', va='top', fontsize=6.5); ax.text(10.3, sv + 0.006, 'severe level', va='bottom', fontsize=6.5, color='0.35')
pick = lambda f: list(zip(*[(y, v) for y, v, d, k in zip(Y, ks, debt, ksd) if f(d, k)]))
ax.scatter(*pick(lambda d, k: d), s=15, color='black', zorder=3, label='debt (26)')
ax.scatter(*pick(lambda d, k: k and not d), s=15, facecolors='white', edgecolors='black', linewidths=0.8, zorder=3, label='KS high, no debt (12)')
ax.scatter(*pick(lambda d, k: not k), s=8, color='0.6', zorder=2, label='KS normal (2)')
ax.set_ylim(0.2, max(ks) + 0.04)
finish(fig, ax, 'ks_over_time')
# Fig. 5: accuracy alone
acc = [100 * (1 - float(r['v_Accuracy'])) for r in rows]; accd = [r['deg_Accuracy'] == '1' for r in rows]
fig, ax = axes('Accuracy (%)')
ax.plot(Y, acc, color='0.75', lw=0.8, zorder=1)
ta = 100 * (1 - th['Accuracy'][0]); ax.axhline(ta, color='black', lw=0.8, zorder=0)
ax.text(10.3, ta - 0.3, 'threshold', va='top', fontsize=6.5)
pick = lambda f: list(zip(*[(y, v) for y, v, d, k in zip(Y, acc, debt, accd) if f(d, k)]))
ax.scatter(*pick(lambda d, k: d and not k), s=15, color='black', zorder=3, label='debt, accuracy normal (15)')
ax.scatter(*pick(lambda d, k: d and k), s=15, color='0.55', zorder=3, label='debt, accuracy low (11)')
ax.scatter(*pick(lambda d, k: not d), s=15, facecolors='white', edgecolors='0.3', linewidths=0.8, zorder=2, label='no debt (14)')
ax.set_ylim(min(acc) - 1, max(acc) + 1); ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(2.5))
finish(fig, ax, 'accuracy_over_time')
print('KS range', round(min(ks), 3), round(max(ks), 3))
