"""Graphviz로 작용경로(기전)와 치료 알고리즘 그림을 그리는 도우미.

사용 예:
    from graphviz_diagram import draw_pathway, draw_algorithm

    draw_pathway(
        [("아라키돈산", "COX-1/2"), ("COX-1/2", "PGH2"),
         ("NSAIDs", "COX-1/2", "억제", "inhibit")],
        "nsaid_moa.png",
        title="NSAIDs 작용기전",
    )

    draw_algorithm(
        {"start": ("고혈압 진단", "start"),
         "q1": ("동반질환 있음?", "decision"),
         "acei": ("ACEi/ARB", "drug"),
         "thz": ("Thiazide 또는 CCB", "drug")},
        [("start", "q1"), ("q1", "acei", "예"), ("q1", "thz", "아니오")],
        "htn_algorithm.png",
        title="고혈압 1차 치료",
    )

출력 형식은 파일 확장자로 정한다(.png, .svg, .pdf).
Graphviz 실행파일(dot)이 PATH에 없으면 흔한 설치 위치를 PATH에 추가한다.
"""

import os
import shutil
import sys
from pathlib import Path

import graphviz

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

if sys.platform == "win32":
    FONT = "Malgun Gothic"
elif sys.platform == "darwin":
    FONT = "Apple SD Gothic Neo"
else:
    FONT = "NanumGothic"
FONT = os.environ.get("PHARMA_FIG_FONT_NAME", FONT)

# 노드 종류별 모양/색
NODE_STYLES = {
    "default":  {"shape": "box", "style": "rounded,filled", "fillcolor": "#F2F4F7"},
    "drug":     {"shape": "box", "style": "rounded,filled", "fillcolor": "#DCEBFF", "color": "#2F6FDB"},
    "target":   {"shape": "ellipse", "style": "filled", "fillcolor": "#FFF1C9", "color": "#C9930A"},
    "effect":   {"shape": "box", "style": "filled", "fillcolor": "#DFF5E3", "color": "#2E8B57"},
    "adverse":  {"shape": "box", "style": "filled", "fillcolor": "#FDE2E1", "color": "#C0392B"},
    "start":    {"shape": "box", "style": "rounded,filled,bold", "fillcolor": "#E8E8E8"},
    "end":      {"shape": "box", "style": "rounded,filled,bold", "fillcolor": "#E8E8E8"},
    "decision": {"shape": "diamond", "style": "filled", "fillcolor": "#FFF1C9", "color": "#C9930A"},
    "action":   {"shape": "box", "style": "filled", "fillcolor": "#F2F4F7"},
}

# 간선 종류별 화살표
EDGE_STYLES = {
    "activate": {"arrowhead": "normal"},
    "inhibit":  {"arrowhead": "tee", "color": "#C0392B", "fontcolor": "#C0392B", "penwidth": "1.6"},
    "convert":  {"arrowhead": "normal", "style": "bold"},
    "indirect": {"arrowhead": "normal", "style": "dashed"},
}


def _new_graph(title, rankdir):
    g = graphviz.Digraph()
    g.attr(rankdir=rankdir, fontname=FONT, labelloc="t", fontsize="18", pad="0.3",
           nodesep="0.4", ranksep="0.5")
    if title:
        g.attr(label=title)
    g.attr("node", fontname=FONT, fontsize="12", margin="0.15,0.07")
    g.attr("edge", fontname=FONT, fontsize="10")
    return g


def _add_edge(g, edge):
    src, dst, *rest = edge
    label = rest[0] if len(rest) > 0 else ""
    kind = rest[1] if len(rest) > 1 else "activate"
    g.edge(src, dst, label=label, **EDGE_STYLES[kind])


def _render(g, filename, dpi):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = path.suffix.lstrip(".").lower() or "png"
    if fmt == "png":
        g.attr(dpi=str(dpi))
    return Path(g.render(outfile=str(path), format=fmt, cleanup=True))


def draw_pathway(edges, filename, title="", node_types=None, rankdir="LR", dpi=200):
    """작용경로/기전 그림을 저장하고 저장 경로를 돌려준다.

    edges: (출발, 도착[, 라벨[, 종류]]) 목록. 종류는 activate(기본), inhibit(⊣),
           convert(굵은 화살표), indirect(점선).
    node_types: {노드이름: 종류} — drug, target, effect, adverse, default 중 하나.
    """
    node_types = node_types or {}
    g = _new_graph(title, rankdir)
    seen = []
    for src, dst, *_ in edges:
        for name in (src, dst):
            if name not in seen:
                seen.append(name)
    for name in seen:
        g.node(name, **NODE_STYLES[node_types.get(name, "default")])
    for edge in edges:
        _add_edge(g, edge)
    return _render(g, filename, dpi)


def draw_algorithm(nodes, edges, filename, title="", rankdir="TB", dpi=200):
    """치료 알고리즘(흐름도)을 저장하고 저장 경로를 돌려준다.

    nodes: {id: (표시 텍스트, 종류)} — 종류는 start, decision, action, drug, end 등.
    edges: (출발 id, 도착 id[, 라벨[, 종류]]) 목록. 라벨에는 보통 "예"/"아니오".
    """
    g = _new_graph(title, rankdir)
    for node_id, (text, kind) in nodes.items():
        g.node(node_id, label=text, **NODE_STYLES[kind])
    for edge in edges:
        _add_edge(g, edge)
    return _render(g, filename, dpi)


if __name__ == "__main__":
    out = Path(__file__).parent / "examples"
    print(draw_pathway(
        [
            ("막 인지질", "아라키돈산", "PLA2", "convert"),
            ("아라키돈산", "COX-1/2"),
            ("COX-1/2", "PGH2", "", "convert"),
            ("PGH2", "PGE2/PGI2"),
            ("PGH2", "TXA2"),
            ("PGE2/PGI2", "통증·발열·염증"),
            ("PGE2/PGI2", "위점막 보호"),
            ("TXA2", "혈소판 응집"),
            ("NSAIDs", "COX-1/2", "억제", "inhibit"),
        ],
        out / "nsaid_moa.png",
        title="NSAIDs 작용기전",
        node_types={"NSAIDs": "drug", "COX-1/2": "target", "통증·발열·염증": "effect",
                    "위점막 보호": "adverse", "혈소판 응집": "effect"},
    ))
    print(draw_algorithm(
        {
            "start": ("고혈압 진단\n(생활습관 교정 병행)", "start"),
            "q1": ("당뇨/CKD\n동반?", "decision"),
            "acei": ("ACEi 또는 ARB", "drug"),
            "first": ("Thiazide / CCB /\nACEi / ARB 중 선택", "drug"),
            "q2": ("목표 혈압\n도달?", "decision"),
            "keep": ("유지 및 추적 관찰", "end"),
            "combo": ("다른 계열 병용 추가", "action"),
        },
        [
            ("start", "q1"),
            ("q1", "acei", "예"),
            ("q1", "first", "아니오"),
            ("acei", "q2"),
            ("first", "q2"),
            ("q2", "keep", "예"),
            ("q2", "combo", "아니오"),
            ("combo", "q2", "", "indirect"),
        ],
        out / "htn_algorithm.png",
        title="고혈압 1차 약물치료 (예시)",
    ))
