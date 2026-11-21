# Draws Fig. 4 of the paper: MMD, KS, and accuracy of MLP_Weather in the 40 monitored years.
# Usage: python code/oe_figure.py results/monitor results/figures
import csv, json, os, sys
import matplotlib
matplotlib.use('Agg')  # draw without a display
import matplotlib.pyplot as plt
from matplotlib import font_manager

MON, OUT = sys.argv[1], sys.argv[2]  # input folder of monitor results, output folder
os.makedirs(OUT, exist_ok=True)  # create the output folder if needed
fams = {f.name for f in font_manager.fontManager.ttflist}  # installed font families
plt.rcParams.update({'font.family': 'FreeSerif' if 'FreeSerif' in fams else 'DejaVu Serif', 'font.size': 7.5,
                     'axes.linewidth': 0.6, 'pdf.fonttype': 42})  # serif font, thin axes, embedded fonts

rows = list(csv.DictReader(open(MON + '/monitor_years_MLP_Weather.csv')))  # one row per monitored year
th = json.load(open(MON + '/monitor_summary_MLP_Weather.json'))['thresholds']  # [threshold, severe level] per metric
Y = [int(r['year']) for r in rows]  # monitored years 11 to 50
oe = [r['Operating_Envelope'] == 'detected' for r in rows]  # years with Operating Envelope
rob = [r['Robustness_Debt'] == 'detected' and not o for r, o in zip(rows, oe)]  # years with Robustness only
none = [not o and not b for o, b in zip(oe, rob)]  # years with no debt

panels = [('MMD', [float(r['v_MMD']) for r in rows], th['MMD'][0], th['MMD'][1]),
          ('KS', [float(r['v_KS']) for r in rows], th['KS'][0], th['KS'][1]),
          ('Accuracy (%)', [100 * (1 - float(r['v_Accuracy'])) for r in rows], 100 * (1 - th['Accuracy'][0]), None)]  # name, values, threshold, severe level

fig, axs = plt.subplots(3, 1, figsize=(3.45, 2.35), sharex=True)  # three stacked panels on one time axis
for ax, (name, v, t, sv) in zip(axs, panels):
    ax.plot(Y, v, color='0.75', lw=0.8, zorder=1)  # value of each year
    ax.axhline(t, color='black', lw=0.8, zorder=0)  # threshold
    if sv is not None:
        ax.axhline(sv, color='0.45', lw=0.8, ls=(0, (1, 1.5)), zorder=0)  # severe level
    pick = lambda m: ([y for y, k in zip(Y, m) if k], [x for x, k in zip(v, m) if k])  # years and values of one group
    ax.scatter(*pick(oe), s=12, color='black', zorder=3, label='Operating Envelope (25)')
    ax.scatter(*pick(rob), s=16, marker='^', color='0.45', zorder=3, label='Robustness only (year 21)')
    ax.scatter(*pick(none), s=12, facecolors='white', edgecolors='black', linewidths=0.7, zorder=2, label='no debt (14)')
    ax.set_ylabel(name)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)  # remove the top and right frame
    ax.tick_params(width=0.6, length=2.5)
axs[0].legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=6.3, frameon=False,
              handletextpad=0.2, columnspacing=0.7, borderaxespad=0.2)  # one legend for all panels
axs[2].set_xlim(10, 51); axs[2].set_xticks([11, 15, 20, 25, 30, 35, 40, 45, 50]); axs[2].set_xlabel('Monitored year')
fig.tight_layout(pad=0.2, h_pad=0.3)
fig.savefig(OUT + '/oe_detection.pdf'); fig.savefig(OUT + '/oe_detection.png', dpi=200)
print('OE', sum(oe), 'Robustness only', sum(rob), 'no debt', sum(none))
