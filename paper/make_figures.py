"""
Publication-quality figures for the paper (vector PDF). Each supports a specific claim:
  fig_frontier  -> the identifiability frontier (Z_eff vs n by censoring)   [Sec 5]
  fig_funnel    -> screening funnel + category split (the sparsity finding)  [Sec 7]
  fig_severity  -> heterogeneity of the in-boundary paid cases (log-$ scale) [Sec 7]
Honest: frontier uses validated Eq.(4); severity points are illustrative/pending verification.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25,
    "grid.linewidth": 0.5, "figure.dpi": 200,
})
OUT = "paper/figures"; os.makedirs(OUT, exist_ok=True)
CB = ["#0072B2", "#E69F00", "#009E73", "#D55E00"]  # colorblind-safe

# ---------- Fig 1: identifiability frontier ----------
k = 6.25
n = np.linspace(1, 120, 400)
levels = [("no censoring", 1.000, CB[0]), ("25th-pct", 0.535, CB[1]),
          ("median", 0.363, CB[2]), ("75th-pct", 0.242, CB[3])]
fig, ax = plt.subplots(figsize=(5.0, 3.4))
for lab, omd, c in levels:
    Z = n*omd / (n*omd + k)
    ax.plot(n, Z, color=c, lw=1.8, label=f"{lab} (1$-\\delta$={omd:.2f})")
    nstar = k/omd
    if nstar <= 120:
        ax.plot([nstar],[0.5], "o", color=c, ms=4)
ax.axhline(0.5, color="0.4", ls="--", lw=0.9)
ax.axvspan(1, 14, color="0.85", alpha=0.5, zorder=0)
ax.text(6.5, 0.93, "current public\nevidence", ha="center", va="top", fontsize=7, color="0.3")
ax.set_xlabel("$n$ (in-boundary monetised cases)")
ax.set_ylabel("credibility $Z_{\\mathrm{eff}}$")
ax.set_title("Identifiability frontier: data- vs prior-driven ($Z{=}0.5$)", fontsize=9.5)
ax.set_xlim(1, 120); ax.set_ylim(0, 1)
ax.legend(fontsize=7, frameon=False, loc="lower right")
ax.annotate("prior-driven", (3, 0.18), fontsize=7.5, color="0.3", style="italic")
ax.annotate("data-driven", (95, 0.82), fontsize=7.5, color="0.3", style="italic", ha="right")
fig.tight_layout(); fig.savefig(f"{OUT}/fig_frontier.pdf"); fig.savefig(f"{OUT}/fig_frontier.png", dpi=200); plt.close(fig)

# ---------- Fig 2: screening funnel + category split ----------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 3.0), gridspec_kw={"width_ratios":[1,1.25]})
# funnel
stages = ["AIID\nincidents", "in-boundary\ncandidates", "genuine\nservice-loss", "paid, with\nfigure"]
vals = [1505, 181, 28, 10]
ypos = np.arange(len(stages))[::-1]
a1.barh(ypos, vals, color=CB[0], alpha=0.85, height=0.6)
a1.set_yticks(ypos); a1.set_yticklabels(stages, fontsize=7.5)
a1.set_xscale("log"); a1.set_xlabel("count (log scale)")
for y, v in zip(ypos, vals):
    a1.text(v*1.15, y, f"{v:,}", va="center", fontsize=8)
a1.set_title("Screening funnel", fontsize=9.5); a1.grid(axis="y", alpha=0)
# category split of the 181
cats = ["copyright/IP\ndemands", "regulatory\nfines", "other", "service–loss", "lawyer\nsanctions"]
cvals = [75, 35, 27, 28, 16]
order = np.argsort(cvals)
a2.barh(np.array(cats)[order], np.array(cvals)[order],
        color=["#999999" if c!="service–loss" else CB[2] for c in np.array(cats)[order]])
for i, v in enumerate(np.array(cvals)[order]):
    a2.text(v+1, i, str(v), va="center", fontsize=8)
a2.set_xlabel("incidents"); a2.set_title("Of 181 in-boundary: mostly not severity", fontsize=9.5)
a2.grid(axis="y", alpha=0)
fig.tight_layout(); fig.savefig(f"{OUT}/fig_funnel.pdf"); fig.savefig(f"{OUT}/fig_funnel.png", dpi=200); plt.close(fig)

# ---------- Fig 3: severity heterogeneity (illustrative) ----------
cases = [("Air Canada chatbot", 812*0.74, "award"),      # CAD$812 ~ US$600
         ("ChatGPT defamation (US)", 50000, "award"),
         ("ChatGPT mayor defamation", 400000*0.66, "demand"),  # AUD$400k ~ US$264k
         ("Meta AI false claims", 5_000_000, "settlement"),
         ("Google Bard/Gemini false claims", 15_000_000, "settlement")]
fig, ax = plt.subplots(figsize=(5.6, 2.7))
xs = [c[1] for c in cases]; ys = np.arange(len(cases))[::-1]
mk = {"award":"o","settlement":"s","demand":"^"}
for (lab,val,typ),y in zip(cases,ys):
    ax.scatter(val, y, s=55, color=CB[0], marker=mk[typ], zorder=3)
    ax.text(val*1.3, y, lab, va="center", fontsize=7.5)
ax.set_yticks([]); ax.set_ylim(-0.8, len(cases)-0.2); ax.set_xscale("log")
ax.set_xlim(200, 5e9); ax.set_xlabel("disclosed amount (US\\$, log scale; illustrative)")
ax.set_title("In-boundary paid cases span $\\sim$4 orders of magnitude", fontsize=9.5)
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([],[],marker=m,color=CB[0],ls="",label=l)
                   for l,m in [("award","o"),("settlement","s"),("demand","^")]],
          fontsize=7, frameon=False, loc="upper left")
fig.tight_layout(); fig.savefig(f"{OUT}/fig_severity.pdf"); fig.savefig(f"{OUT}/fig_severity.png", dpi=200); plt.close(fig)

print("Wrote:", ", ".join(os.listdir(OUT)))
