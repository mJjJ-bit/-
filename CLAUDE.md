# 작업 규칙

## 약학 공부자료 그림

화학 구조식이나 작용경로·순환경로·치료 알고리즘 그림이 필요하면 **matplotlib이나 손으로 그린 SVG를 쓰지 말고**
`pharma-figures/`의 두 도구만 쓴다. 설치·사용법은 `pharma-figures/README.md`.

- 구조식: `rdkit_structure.py`의 `draw_structure(smiles, 파일명, label)`,
  `draw_grid([(라벨, smiles), ...], 파일명, mols_per_row)`
  - 라벨은 RDKit legend가 아니라 PIL + 맑은 고딕으로 그림 아래에 합성한다(legend에 한글을 넣으면 사라짐).
  - 새 SMILES는 먼저 렌더링해서 고리 크기·치환기·입체화학을 눈으로 확인한 뒤 쓴다.
- 경로·알고리즘: `graphviz_pathway.py`의 `new_graph(제목, rankdir, engine)`,
  `add_step(g, id, 라벨, regulated=False)`, `add_edge(...)`, `render(g, 파일명)`
  - 폰트 Malgun Gothic, dpi 180.
  - 색: 네이비 #1F3864(기본선), 주황 #E08E2B(핵심 단계), 초록 #2E8B57(활성), 빨강 #C0392B(억제·금기).
  - 알고리즘·흐름도는 `engine="dot"`(rankdir TB 또는 LR), 순환경로는 `engine="circo"`.

### 그림 품질 규칙

- 한글 라벨은 NFC 정규화된 문자열만 쓴다(자모가 분리되면 글자가 깨진다).
- 문서에 넣을 폭 기준으로 인쇄 글자 크기를 계산해 8pt 이상인지 확인한다:
  `fontsize × 180 × 삽입폭(inch) ÷ PNG 가로 픽셀 ≥ 8`
  작으면 라벨을 여러 줄로 나눠 폭을 줄인다. (`render()`가 계산해서 출력한다.)
- 화살표가 노드에 겹치거나 서로 교차하지 않게 하고, 순서가 없는 항목끼리는 화살표로 잇지 않는다.
- 그린 PNG는 반드시 직접 열어 보고 글자 깨짐·겹침을 확인한다.
