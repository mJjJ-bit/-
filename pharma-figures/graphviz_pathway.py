"""Graphviz로 작용경로·순환경로·치료 알고리즘(흐름도)을 그리는 도우미 (PNG, 180 dpi).

사용 예:
    from graphviz_pathway import new_graph, add_step, add_edge, render

    g = new_graph("NSAIDs 작용기전", rankdir="LR")          # 알고리즘·흐름도: engine="dot"
    add_step(g, "aa", "아라키돈산")
    add_step(g, "cox", "COX-1/2", regulated=True)          # 핵심 단계 → 주황
    add_step(g, "pg", "프로스타글란딘")
    add_step(g, "nsaid", "NSAIDs", color=RED)
    add_edge(g, "aa", "cox")
    add_edge(g, "cox", "pg")
    add_edge(g, "nsaid", "cox", "억제", kind="inhibit")    # 빨강 ⊣
    render(g, "nsaid_moa.png", insert_width_in=6)

    g = new_graph("엽산 회로", engine="circo")              # 순환경로

규칙
- 라벨은 NFC 정규화된 문자열만 쓴다(add_step/add_edge가 자동으로 정규화).
- 순서가 없는 항목끼리는 화살표로 잇지 않는다.
- render()는 문서 삽입폭 기준 인쇄 글자 크기를 계산해 8pt 미만이면 경고한다.
  (fontsize × 180 × 삽입폭(inch) ÷ PNG 가로 픽셀 ≥ 8) 작으면 라벨을 "\\n"으로 나눌 것.
- 렌더링한 PNG는 반드시 직접 열어 글자 깨짐·겹침을 확인한다.
"""

import os
import shutil
import sys
import unicodedata
from pathlib import Path

import graphviz
from PIL import Image

NAVY = "#1F3864"    # 기본선
ORANGE = "#E08E2B"  # 핵심 단계(속도결정·조절 단계)
GREEN = "#2E8B57"   # 활성
RED = "#C0392B"     # 억제·금기

DPI = 180
FONT = os.environ.get("PHARMA_FIG_FONT_NAME", "Malgun Gothic")
NODE_FONTSIZE = 12
MIN_PRINT_PT = 8

_GRAPHVIZ_BIN_CANDIDATES = [
    r"C:\Program Files\Graphviz\bin",
    r"C:\Program Files (x86)\Graphviz\bin",
    "/opt/homebrew/bin",
    "/usr/local/bin",
]


def _ensure_dot_on_path():
    if shutil.which("dot"):
        return
    for folder in _GRAPHVIZ_BIN_CANDIDATES:
        if Path(folder, "dot.exe").exists() or Path(folder, "dot").exists():
            os.environ["PATH"] = folder + os.pathsep + os.environ.get("PATH", "")
            return
    print("경고: Graphviz 'dot'을 찾지 못함. Windows는 'winget install Graphviz.Graphviz' 후 "
          "터미널을 다시 여세요.", file=sys.stderr)


_ensure_dot_on_path()


def _nfc(text):
    return unicodedata.normalize("NFC", text)


def new_graph(title="", rankdir="TB", engine="dot"):
    """새 그래프. 알고리즘·흐름도는 engine="dot"(rankdir TB/LR), 순환경로는 engine="circo"."""
    g = graphviz.Digraph(engine=engine)
    g.attr(rankdir=rankdir, dpi=str(DPI), fontname=FONT, fontsize="16", fontcolor=NAVY,
           labelloc="t", pad="0.25", nodesep="0.45", ranksep="0.55", splines="spline")
    if engine == "circo":
        g.attr(mindist="0.7")  # 순환경로가 지나치게 넓어져 글자가 작아지는 것을 막음
    if title:
        g.attr(label=_nfc(title))
    g.attr("node", shape="box", style="rounded,filled", fillcolor="white", color=NAVY,
           fontname=FONT, fontsize=str(NODE_FONTSIZE), fontcolor=NAVY, penwidth="1.4",
           margin="0.15,0.07")
    g.attr("edge", color=NAVY, fontname=FONT, fontsize="10", fontcolor=NAVY,
           penwidth="1.2", arrowsize="0.8")
    return g


def add_step(g, node_id, label, regulated=False, **attrs):
    """단계(노드)를 추가. regulated=True면 핵심 단계로 주황 강조.

    attrs로 Graphviz 노드 속성을 덮어쓸 수 있다(예: shape="diamond", color=RED).
    """
    style = {}
    if regulated:
        style = {"color": ORANGE, "fillcolor": "#FCEBD5", "penwidth": "2.2"}
    if "color" in attrs and "fontcolor" not in attrs:
        attrs["fontcolor"] = attrs["color"]
    g.node(node_id, label=_nfc(label), **{**style, **attrs})


def add_edge(g, src, dst, label="", kind="default", **attrs):
    """화살표 추가. kind: default(네이비 →), activate(초록 →), inhibit(빨강 ⊣)."""
    style = {
        "default": {},
        "activate": {"color": GREEN, "fontcolor": GREEN},
        "inhibit": {"color": RED, "fontcolor": RED, "arrowhead": "tee", "penwidth": "1.6"},
    }[kind]
    g.edge(src, dst, label=_nfc(label), **{**style, **attrs})


def render(g, filename, insert_width_in=6.0):
    """PNG로 저장하고 경로를 돌려준다. 삽입폭 기준 인쇄 글자 크기가 8pt 미만이면 경고."""
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = Path(g.render(outfile=str(path), format="png", cleanup=True))
    with Image.open(out) as img:
        png_width = img.width
    pt = NODE_FONTSIZE * DPI * insert_width_in / png_width
    status = "OK" if pt >= MIN_PRINT_PT else "너무 작음 → 라벨을 여러 줄로 나눠 폭을 줄이세요"
    print(f"{out.name}: {png_width}px, 삽입폭 {insert_width_in}in에서 인쇄 {pt:.1f}pt ({status})",
          file=sys.stderr if pt < MIN_PRINT_PT else sys.stdout)
    return out


if __name__ == "__main__":
    out_dir = Path(__file__).parent / "examples"

    # 1) 치료 알고리즘(흐름도): dot, TB
    g = new_graph("고혈압 1차 약물치료 (예시)", rankdir="TB")
    add_step(g, "dx", "고혈압 진단\n(생활습관 교정 병행)")
    add_step(g, "q1", "당뇨·CKD\n동반?", shape="diamond", style="filled")
    add_step(g, "acei", "ACEi 또는 ARB", regulated=True)
    add_step(g, "first", "Thiazide · CCB ·\nACEi · ARB 중 선택")
    add_step(g, "preg", "임신 시 ACEi·ARB\n금기", color=RED)
    add_step(g, "q2", "목표 혈압\n도달?", shape="diamond", style="filled")
    add_step(g, "keep", "유지·추적 관찰", color=GREEN)
    add_step(g, "combo", "다른 계열\n병용 추가")
    add_edge(g, "dx", "q1")
    add_edge(g, "q1", "acei", "예")
    add_edge(g, "q1", "first", "아니오")
    add_edge(g, "acei", "preg", "", kind="inhibit", style="dashed", arrowhead="none")
    add_edge(g, "acei", "q2")
    add_edge(g, "first", "q2")
    add_edge(g, "q2", "keep", "예", kind="activate")
    add_edge(g, "q2", "combo", "아니오")
    add_edge(g, "combo", "q2", style="dashed", constraint="false")
    render(g, out_dir / "htn_algorithm.png", insert_width_in=4.5)

    # 2) 순환경로: circo
    g = new_graph("엽산 회로와 항대사제", engine="circo")
    add_step(g, "dhf", "DHF")
    add_step(g, "dhfr", "DHFR", regulated=True)
    add_step(g, "thf", "THF")
    add_step(g, "mthf", "5,10-메틸렌\n-THF")
    add_step(g, "ts", "Thymidylate\nsynthase", regulated=True)
    add_step(g, "mtx", "Metho-\ntrexate", color=RED)
    add_step(g, "fu", "5-FU", color=RED)
    add_edge(g, "dhf", "dhfr")
    add_edge(g, "dhfr", "thf")
    add_edge(g, "thf", "mthf")
    add_edge(g, "mthf", "ts")
    add_edge(g, "ts", "dhf", "dUMP\n→ dTMP")
    add_edge(g, "mtx", "dhfr", kind="inhibit")
    add_edge(g, "fu", "ts", kind="inhibit")
    render(g, out_dir / "folate_cycle.png", insert_width_in=4.5)
