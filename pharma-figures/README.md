# pharma-figures

약학 공부자료용 그림 도우미. 화학 구조식은 **RDKit**, 작용경로·치료 알고리즘은 **Graphviz**로만 그린다
(matplotlib이나 손으로 그린 SVG는 쓰지 않음).

## 설치

```bash
pip install -r requirements.txt          # rdkit, graphviz, pillow
```

Graphviz 실행파일(`dot`)도 따로 설치해야 한다.

| OS | 명령 |
|---|---|
| Windows | `winget install Graphviz.Graphviz` (설치 후 터미널 재시작) |
| macOS | `brew install graphviz` |
| Ubuntu | `sudo apt install graphviz fonts-nanum` |

`dot`이 PATH에 없으면 `graphviz_diagram.py`가 `C:\Program Files\Graphviz\bin` 등을 `os.environ["PATH"]`에 직접 추가한다.

## 사용법

```python
from rdkit_structure import draw_structure, draw_grid
from graphviz_diagram import draw_pathway, draw_algorithm

draw_structure("CC(=O)Oc1ccccc1C(=O)O", "aspirin.png", "Aspirin (아스피린)")
draw_grid([("Ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
           ("Naproxen", "COc1ccc2cc(ccc2c1)C(C)C(=O)O")], "nsaids.png", mols_per_row=2)

# 간선: (출발, 도착[, 라벨[, 종류]])  종류 = activate | inhibit(⊣) | convert | indirect
draw_pathway([("아라키돈산", "COX-1/2"), ("COX-1/2", "PGH2"),
              ("NSAIDs", "COX-1/2", "억제", "inhibit")],
             "nsaid_moa.png", title="NSAIDs 작용기전",
             node_types={"NSAIDs": "drug", "COX-1/2": "target"})

# 노드: {id: (텍스트, 종류)}  종류 = start | decision | action | drug | end
draw_algorithm({"s": ("고혈압 진단", "start"), "q": ("CKD 동반?", "decision"),
                "a": ("ACEi/ARB", "drug"), "b": ("Thiazide/CCB", "drug")},
               [("s", "q"), ("q", "a", "예"), ("q", "b", "아니오")],
               "htn.png", title="고혈압 1차 치료")
```

- 출력 형식은 확장자로 결정: 구조식 `.png`/`.svg`, 다이어그램 `.png`/`.svg`/`.pdf`.
- 노드 종류(경로): `drug`(파랑), `target`(노랑 타원), `effect`(초록), `adverse`(빨강), `default`.
- 한글 라벨: RDKit 자체 글꼴은 한글을 □로 그리므로, 한글이 들어간 라벨은 같은 legend 자리에
  시스템 한글 폰트로 덧그린다. 폰트를 못 찾으면 `PHARMA_FIG_FONT`(구조식용 .ttf 경로),
  `PHARMA_FIG_FONT_NAME`(Graphviz용 폰트 이름) 환경변수로 지정.
- `python rdkit_structure.py`, `python graphviz_diagram.py`를 실행하면 `examples/`에 예시 그림이 생긴다.
