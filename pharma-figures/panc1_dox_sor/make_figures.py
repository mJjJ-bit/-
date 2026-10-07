"""PANC-1 DOX+SOR 포스터 Fig 3–6 (CompuSyn 결과 그래프).

수치는 같은 폴더의 compusyn_report.html(CompuSyn Report)에서 compusyn_report.py로 읽는다.
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
from compusyn_report import load_report  # noqa: E402

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

# ── CompuSyn 결과: compusyn_report.html(CompuSyn Report 내보내기)에서 직접 읽는다 ──
REPORT = load_report(OUT / "compusyn_report.html")
PARAMS = {k: (v["Dm"], v["m"]) for k, v in REPORT["params"].items()}  # 병용은 총농도 기준
OBS = {
    "SOR": REPORT["dose_effect"]["SOR"],
    "DOX": REPORT["dose_effect"]["DOX"],
    # 병용 실측점은 보고서의 Dose A(SOR) 대신 CI 표의 총농도(SOR+DOX)로 그린다
    "DOX+SOR": [(total, fa) for total, fa, _ in REPORT["ci_points"]],
}
FA, CI = np.array([(fa, ci) for fa, ci, _ in REPORT["ci_curve"]]).T
CI_OBS = [(fa, ci) for _, fa, ci in REPORT["ci_points"]]
_dri = np.array(REPORT["dri_curve"])
DRI_FA, DRI_SOR, DRI_DOX = _dri[:, 0], _dri[:, 3], _dri[:, 4]
_dri_obs = np.array(REPORT["dri_points"])
DRI_OBS_FA, DRI_OBS_SOR, DRI_OBS_DOX = _dri_obs[:, 0], _dri_obs[:, 3], _dri_obs[:, 4]
ISO = [  # (라벨, x = D(SOR)/Dx(SOR), y = D(DOX)/Dx(DOX), CI)
    (f"ED{round(fa * 100)}", e["combo"]["SOR"] / e["Dx"]["SOR"],
     e["combo"]["DOX"] / e["Dx"]["DOX"], e["CI"])
    for fa, e in REPORT["ed"].items() if fa in (0.5, 0.75, 0.9)
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
        x, y = np.array(OBS[name]).T
        ax.plot(d, 1 / (1 + (dm / d) ** m), color=COLORS[name], lw=2.4,
                label=name + (" (total dose)" if name == "DOX+SOR" else ""))
        ax.scatter(x, y, marker=MARKERS[name], s=70, facecolors="white",
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
    ax.plot(DRI_FA, DRI_SOR, color=NAVY, lw=2.6, zorder=2)
    ax.plot(DRI_FA, DRI_DOX, color=RED, lw=2.6, zorder=2)
    # 실측점에서 계산한 DRI (CompuSyn "DRI values calculated at experimental points")
    ax.scatter(DRI_OBS_FA, DRI_OBS_SOR, marker="o", s=70, facecolors="white", edgecolors=NAVY,
               linewidths=2, zorder=3)
    ax.scatter(DRI_OBS_FA, DRI_OBS_DOX, marker="s", s=70, facecolors="white", edgecolors=RED,
               linewidths=2, zorder=3)
    ax.text(0.575, 1100, "Model: both DRI > 1\n(Fa 0.40–0.75)", color=NAVY, fontsize=ANNOT_PT,
            ha="center", va="center")
    ax.set_yscale("log")
    ax.set_ylim(0.03, 5000)
    _log_ticks(ax, [0.1, 1, 10, 100, 1000])
    ax.set_xlim(0, 1.02)
    ax.set_xlabel("Fa")
    ax.set_ylabel("DRI (log scale)")
    handles = [plt.Line2D([], [], color=c, lw=2.6, marker=mk, ms=9, mfc="white", mew=2)
               for c, mk in ((NAVY, "o"), (RED, "s"))]
    ax.legend(handles, ["DRI (SOR)", "DRI (DOX)"], loc="upper left", labelcolor=NAVY)
    return _save(fig, "fig6_dri_fa.png")


if __name__ == "__main__":
    print(f"font: {FONT}")
    for draw in (fig3_dose_effect, fig4_ci_fa, fig5_isobologram, fig6_dri_fa):
        draw()
