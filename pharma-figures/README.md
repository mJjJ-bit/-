# pharma-figures

약학 공부자료용 그림 도우미. 화학 구조식은 **RDKit**(`rdkit_structure.py`), 작용경로·순환경로·치료 알고리즘은
**Graphviz**(`graphviz_pathway.py`)로만 그린다. matplotlib이나 손으로 그린 SVG는 쓰지 않는다.

## 설치

```bash
pip install -r requirements.txt          # rdkit, graphviz, pillow
winget install Graphviz.Graphviz         # Windows: dot 실행파일 (설치 후 터미널 재시작)
# macOS: brew install graphviz   /   Ubuntu: sudo apt install graphviz fonts-nanum
```

`dot`이 PATH에 없으면 `graphviz_pathway.py`가 `C:\Program Files\Graphviz\bin` 등을 `os.environ["PATH"]`에 추가한다.

## 구조식 — `rdkit_structure.py`

```python
from rdkit_structure import draw_structure, draw_grid

draw_structure("CC(=O)Oc1ccccc1C(=O)O", "aspirin.png", "Aspirin\n(아스피린)")
draw_grid([("Ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
           ("(S)-Naproxen", "COc1ccc2cc(ccc2c1)[C@H](C)C(=O)O")],
          "nsaids.png", mols_per_row=2)
```

- 라벨은 RDKit legend가 아니라 PIL + 맑은 고딕으로 그림 아래에 합성한다(legend에 한글을 넣으면 사라짐).
- 라벨은 자동으로 NFC 정규화되고, `"\n"`으로 여러 줄을 쓸 수 있다.
- `insert_width_in`(문서 삽입폭, 기본: 단일 3in·격자 6in) 기준 라벨 인쇄 크기가 8pt 미만이면 경고한다.

## 경로·알고리즘 — `graphviz_pathway.py`

```python
from graphviz_pathway import new_graph, add_step, add_edge, render, RED

g = new_graph("NSAIDs 작용기전", rankdir="LR", engine="dot")   # 흐름도: dot / 순환경로: circo
add_step(g, "aa", "아라키돈산")
add_step(g, "cox", "COX-1/2", regulated=True)                 # 핵심 단계 → 주황
add_step(g, "pg", "프로스타글란딘")
add_step(g, "nsaid", "NSAIDs", color=RED)
add_edge(g, "aa", "cox"); add_edge(g, "cox", "pg")
add_edge(g, "nsaid", "cox", "억제", kind="inhibit")           # 빨강 ⊣
render(g, "nsaid_moa.png", insert_width_in=6)                 # 인쇄 pt 계산·경고 출력
```

| 색 | 용도 |
|---|---|
| 네이비 `#1F3864` | 기본선·기본 노드 |
| 주황 `#E08E2B` | 핵심 단계 (`regulated=True`) |
| 초록 `#2E8B57` | 활성 (`kind="activate"`, `color=GREEN`) |
| 빨강 `#C0392B` | 억제·금기 (`kind="inhibit"`, `color=RED`) |

폰트 Malgun Gothic, PNG 180 dpi. `add_step`/`add_edge`의 추가 키워드는 Graphviz 속성으로 그대로 전달된다
(예: 결정 노드 `shape="diamond", style="filled"`).

`python rdkit_structure.py`, `python graphviz_pathway.py`를 실행하면 `examples/`에 예시 그림이 생긴다.
