"""PANC-1 DOX+SOR 포스터 Fig 3–6 (CompuSyn 결과 그래프).

수치는 인계 자료(PANC1_DOX_SOR_poster_handoff.md) 3장의 CompuSyn 결과를 그대로 쓴다.
수치 그래프라서 matplotlib으로 그리되, 글꼴·색·dpi는 pharma-figures 세팅을 따른다.
  - 글꼴 Malgun Gothic(없으면 다른 한글 폰트), dpi 180
  - 색: 네이비 #1F3864, 주황 #E08E2B, 초록 #2E8B57, 빨강 #C0392B
  - 크기: 포스터 그림 칸(7.4 × 5.47 in) 그대로 → 인쇄 글자 크기 = 지정 pt

실행: python make_figures.py  →  같은 폴더에 fig3.png … fig6.png
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from graphviz_pathway import DPI, GREEN, NAVY, ORANGE, RED  # noqa: E402

FIG_SIZE_IN = (7.4, 5.47)  # 포스터 그림 칸 크기
MIN_PRINT_PT = 8
ANNOT_PT = 15  # 그래프 안 주석 글자 크기
OUT = Path(__file__).resolve().parent

_installed = {f.name for f in font_manager.fontManager.ttflist}
FONT = next((f for f in ("Malgun Gothic", "NanumGothic", "Noto Sans CJK KR") if f in _installed),
            "sans-serif")

plt.rcParams.update({
    # µ·지수의 − 같은 기호가 한글 폰트에 없으면 DejaVu Sans로 대체
    "font.family": [FONT, "DejaVu Sans"],
    "mathtext.fontset": "dejavusans",
    "axes.unicode_minus": False,
    "font.size": 16,
    "axes.labelsize": 19,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
    "legend.fontsize": 15,
    "axes.edgecolor": NAVY,
    "axes.labelcolor": NAVY,
    "xtick.color": NAVY,
    "ytick.color": NAVY,
    "axes.linewidth": 1.4,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "savefig.dpi": DPI,
})

SYNERGY_TINT = "#DCEFE3"   # 초록 #2E8B57의 옅은 바탕
KEY_TINT = "#FCEBD5"       # 주황 #E08E2B의 옅은 바탕

# ── CompuSyn 결과 (인계 자료 3장) ───────────────────────────────────
PARAMS = {  # Dm(µg/mL), m
    "SOR": (0.27714, 1.15661),
    "DOX": (0.01958, 0.35984),
    "DOX+SOR": (0.07739, 0.51683),  # 총농도 기준
}
OBS = {
    "SOR": [(4e-4, .00765), (.0015, .06418), (.0058, 1e-5), (.0233, .26132), (.0933, .14835),
            (.3733, .22856), (1.493, .44291), (5.9722, .84693), (23.8886, .99999), (95.5545, .99641)],
    "DOX": [(3.3e-5, .20883), (1.33e-4, .23873), (5.3e-4, .22333), (.00212, .2109), (.0085, .22474),
            (.034, .28595), (.1359, .50255), (.5437, .68225), (2.1749, .93857), (8.6997, .96074)],
    # SOR 용량 기준 → 총농도(×1.2)로 바꿔서 그린다
    "DOX+SOR": [(1.2e-4, .05113), (5e-4, .19308), (.002, .20483), (.0075, .22484), (.031, .24362),
                (.1235, .2793), (.4935, .4367), (1.974, .57983), (7.895, .98683), (31.58, .98831)],
}
FA = np.array([.05, .10, .15, .20, .25, .30, .35, .40, .45, .50, .55, .60, .65, .70, .75, .80,
               .85, .90, .95, .97])
CI = np.array([7.92029, 4.23188, 2.88506, 2.17579, 1.73707, 1.44091, 1.23084, 1.07839, .96807,
               .89144, .84454, .82695, .84201, .89846, 1.01473, 1.23047, 1.64196, 2.54716, 5.49282,
               9.64148])
CI_OBS = [(.05113, 4.11345), (.19308, .27799), (.20483, .90901), (.22484, 2.46716),
          (.24362, 7.67604), (.2793, 18.5905), (.4367, 12.4462), (.57983, 13.6305),
          (.98683, .6828), (.98831, 2.45954)]
DRI_SOR = np.array([100.425, 45.1358, 27.5096, 18.9489, 13.9272, 10.6426, 8.33578, 6.63243,
                    5.32696, 4.29738, 3.46679, 2.78442, 2.21544, 1.73524, 1.326, .97459, .67131,
                    .40915, .18389, .1041])
DRI_DOX = np.array([.12642, .23755, .35104, .47103, .6005, .74242, .90019, 1.07804, 1.28149,
                    1.51804, 1.79826, 2.13764, 2.55996, 3.10396, 3.83754, 4.89239, 6.56472,
                    9.70111, 18.229, 28.5547])
ISO = [  # (라벨, x = D(SOR)/Dx(SOR), y = D(DOX)/Dx(DOX), CI)
    ("ED50", .06449 / .27714, .0129 / .01958, 0.89),
    ("ED75", .54035 / .7165, .10807 / .41472, 1.01),
    ("ED90", 4.5274 / 1.8524, .90548 / 8.78416, 2.55),
]
COLORS = {"SOR": NAVY, "DOX": RED, "DOX+SOR": GREEN}
MARKERS = {"SOR": "o", "DOX": "s", "DOX+SOR": "^"}


def _new_axes():
    return plt.subplots(figsize=FIG_SIZE_IN, layout="constrained")


def _save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=DPI, facecolor="white")
    plt.close(fig)
    # 인쇄 크기 = fontsize × 180 × 삽입폭 ÷ PNG 가로 픽셀 (가장 작은 글자 기준)
    from PIL import Image
    with Image.open(path) as im:
        px = im.width
    smallest = min(plt.rcParams["xtick.labelsize"], plt.rcParams["legend.fontsize"], ANNOT_PT)
    pt = smallest * DPI * FIG_SIZE_IN[0] / px
    flag = "OK" if pt >= MIN_PRINT_PT else "너무 작음"
    print(f"{name}: {px}px, 삽입폭 {FIG_SIZE_IN[0]}in에서 최소 글자 {pt:.1f}pt ({flag})")
    return path


def _log_ticks(ax, ticks):
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:g}" for t in ticks])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())


def fig3_dose_effect():
    fig, ax = _new_axes()
    d = np.logspace(-5, np.log10(200), 400)
    for name in ("SOR", "DOX", "DOX+SOR"):
        dm, m = PARAMS[name]
        scale = 1.2 if name == "DOX+SOR" else 1.0
        x, y = np.array(OBS[name]).T
        ax.plot(d, 1 / (1 + (dm / d) ** m), color=COLORS[name], lw=2.4,
                label=name + (" (total dose)" if name == "DOX+SOR" else ""))
        ax.scatter(x * scale, y, marker=MARKERS[name], s=70, facecolors="white",
                   edgecolors=COLORS[name], linewidths=2, zorder=3)
    ax.set_xscale("log")
    ax.set_xlim(1e-5, 200)
    # 10의 거듭제곱 표기는 DejaVu 수식 글꼴로(한글 폰트에는 위첨자 −가 없음)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda v, _: rf"$\mathrm{{10^{{{int(round(np.log10(v)))}}}}}$"))
    ax.set_ylim(-0.03, 1.05)
    ax.set_xlabel("Dose (µg/mL, log scale)")
    ax.set_ylabel("Fa (fraction affected)")
    handles = [plt.Line2D([], [], color=COLORS[n], lw=2.4, marker=MARKERS[n], ms=9,
                          mfc="white", mew=2) for n in COLORS]
    ax.legend(handles, ["SOR", "DOX", "DOX+SOR (total dose)"], loc="upper left",
              labelcolor=NAVY)
    return _save(fig, "fig3_dose_effect.png")


def fig4_ci_fa():
    fig, ax = _new_axes()
    ax.axhspan(0.1, 1, color=SYNERGY_TINT, lw=0, zorder=0)
    ax.axhline(1, color=NAVY, lw=1.6, ls=(0, (2, 2)))
    ax.plot(FA, CI, color=GREEN, lw=2.6, label="Fitted-model CI", zorder=2)
    fx, fy = np.array(CI_OBS).T
    ax.scatter(fx, fy, s=70, facecolors="white", edgecolors=NAVY, linewidths=2,
               label="Observed points", zorder=3)
    i = int(np.argmin(CI))
    ax.annotate(f"min CI {CI[i]:.2f}\n(Fa {FA[i]:.2f})", xy=(FA[i], CI[i]),
                xytext=(0.62, 0.3), color=NAVY, fontsize=ANNOT_PT,
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.6))
    # 곡선이 CI<1로 내려가는 구간 위 빈자리에 둔다(곡선과 겹치지 않게)
    ax.text(0.575, 1.6, "Antagonism (CI > 1)", color=RED, fontsize=ANNOT_PT, ha="center",
            va="bottom")
    ax.text(0.02, 0.12, "Synergism (CI < 1)", color=GREEN, fontsize=ANNOT_PT, va="bottom")
    ax.set_yscale("log")
    ax.set_ylim(0.1, 30)
    _log_ticks(ax, [0.1, 0.3, 1, 3, 10, 30])
    ax.set_xlim(0, 1.02)
    ax.set_xlabel("Fa")
    ax.set_ylabel("CI (log scale)")
    ax.legend(loc="upper right", labelcolor=NAVY)
    return _save(fig, "fig4_ci_fa.png")


def fig5_isobologram():
    fig, ax = _new_axes()
    ax.fill([0, 1, 0], [0, 0, 1], color=SYNERGY_TINT, lw=0, zorder=0)
    ax.plot([0, 1], [1, 0], color=NAVY, lw=2.2, label="Additive line (x + y = 1)")
    colors = {"ED50": GREEN, "ED75": ORANGE, "ED90": RED}
    offsets = {"ED50": (0.10, 0.10), "ED75": (0.10, 0.10), "ED90": (-0.05, 0.13)}
    for name, x, y, ci in ISO:
        ax.scatter([x], [y], s=150, color=colors[name], edgecolors="white", linewidths=2,
                   zorder=3)
        dx, dy = offsets[name]
        ax.text(x + dx, y + dy, f"{name}\nCI {ci:.2f}", color=NAVY, fontsize=ANNOT_PT,
                ha="left" if dx > 0 else "center", va="bottom")
    ax.text(0.04, 0.05, "Synergism", color=GREEN, fontsize=ANNOT_PT)
    ax.set_xlim(0, 2.9)
    ax.set_ylim(0, 1.15)
    ax.set_xlabel("D(SOR) / Dx(SOR)")
    ax.set_ylabel("D(DOX) / Dx(DOX)")
    ax.legend(loc="upper right", labelcolor=NAVY)
    return _save(fig, "fig5_isobologram.png")


def fig6_dri_fa():
    fig, ax = _new_axes()
    ax.axvspan(0.4, 0.75, color=KEY_TINT, lw=0, zorder=0)
    ax.axhline(1, color=NAVY, lw=1.6, ls=(0, (2, 2)))
    ax.plot(FA, DRI_SOR, color=NAVY, lw=2.6, label="DRI (SOR)")
    ax.plot(FA, DRI_DOX, color=RED, lw=2.6, label="DRI (DOX)")
    ax.text(0.575, 0.12, "Both DRI > 1\n(Fa 0.40–0.75)", color=NAVY, fontsize=ANNOT_PT,
            ha="center", va="bottom")
    ax.set_yscale("log")
    ax.set_ylim(0.08, 150)
    _log_ticks(ax, [0.1, 1, 10, 100])
    ax.set_xlim(0, 1)
    ax.set_xlabel("Fa")
    ax.set_ylabel("DRI (log scale)")
    ax.legend(loc="upper center", labelcolor=NAVY)
    return _save(fig, "fig6_dri_fa.png")


if __name__ == "__main__":
    print(f"font: {FONT}")
    for draw in (fig3_dose_effect, fig4_ci_fa, fig5_isobologram, fig6_dri_fa):
        draw()
