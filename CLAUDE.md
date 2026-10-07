# 작업 규칙

- 약학 공부자료에 화학 구조식이나 작용경로·치료 알고리즘 그림이 필요하면 matplotlib이나 손으로 그린 SVG를
  쓰지 말고 `pharma-figures/`의 도우미만 사용한다.
  - 구조식: `rdkit_structure.py`의 `draw_structure`, `draw_grid` (SMILES 입력, 라벨은 legend 자리)
  - 작용경로/알고리즘: `graphviz_diagram.py`의 `draw_pathway`, `draw_algorithm`
- 설치와 사용법은 `pharma-figures/README.md` 참고.
