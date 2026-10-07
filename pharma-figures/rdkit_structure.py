"""RDKit으로 약물 화학 구조식을 그리는 도우미 (PNG 출력).

사용 예:
    from rdkit_structure import draw_structure, draw_grid

    draw_structure("CC(=O)Oc1ccccc1C(=O)O", "aspirin.png", "Aspirin (아스피린)")
    draw_grid(
        [("Ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
         ("Naproxen", "COc1ccc2cc(ccc2c1)[C@H](C)C(=O)O")],
        "nsaids.png",
        mols_per_row=2,
    )

라벨은 RDKit legend에 넣지 않는다(한글이 사라짐). 구조식만 RDKit으로 그리고,
라벨은 PIL + 맑은 고딕으로 그림 아래에 합성한다. 라벨은 NFC로 정규화하며,
여러 줄은 "\\n"으로 나눈다.

새 SMILES는 먼저 렌더링해서 고리 크기·치환기·입체화학을 눈으로 확인한 뒤 쓸 것.
"""

import io
import os
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

PNG_DPI = 180
LABEL_FONT_PX = 22
MIN_PRINT_PT = 8

# 맑은 고딕을 우선 쓰고, 없는 환경(Mac/Linux)에서만 다른 한글 폰트로 대체
_KOREAN_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\malgun.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def _load_font(size):
    candidates = [os.environ.get("PHARMA_FIG_FONT", "")] + _KOREAN_FONT_CANDIDATES
    for path in candidates:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size)
    print("경고: 한글 폰트를 찾지 못함. PHARMA_FIG_FONT에 .ttf 경로를 지정하세요.", file=sys.stderr)
    return ImageFont.load_default(size=size)


def _mol_from_smiles(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"SMILES를 해석할 수 없음: {smiles!r}")
    AllChem.Compute2DCoords(mol)
    return mol


def _mol_image(mol, size):
    drawer = rdMolDraw2D.MolDraw2DCairo(*size)
    opts = drawer.drawOptions()
    opts.addStereoAnnotation = True
    opts.padding = 0.08
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return Image.open(io.BytesIO(drawer.GetDrawingText())).convert("RGB")


def _caption_height(lines, font):
    line_h = font.getbbox("가Ag")[3]
    return int(line_h * 1.35 * len(lines)) + 16


def _draw_caption(canvas, lines, font, box):
    """box=(x0, y0, w, h) 영역 가운데에 여러 줄 라벨을 그린다."""
    x0, y0, w, h = box
    draw = ImageDraw.Draw(canvas)
    text = "\n".join(lines)
    draw.multiline_text((x0 + w / 2, y0 + h / 2), text, font=font, fill="black",
                        anchor="mm", align="center", spacing=6)
    widest = max(draw.textlength(line, font=font) for line in lines)
    if widest > w:
        print(f"경고: 라벨이 칸 폭보다 넓음 → 줄을 나누세요: {text!r}", file=sys.stderr)


def _normalize(label):
    return unicodedata.normalize("NFC", label or "").split("\n")


def _save(canvas, filename, insert_width_in):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, dpi=(PNG_DPI, PNG_DPI))
    # 문서에 insert_width_in 인치 폭으로 넣었을 때 라벨의 인쇄 크기(pt)
    pt = LABEL_FONT_PX * 72 * insert_width_in / canvas.width
    if pt < MIN_PRINT_PT:
        print(f"경고: {path.name} 라벨 인쇄 크기 {pt:.1f}pt < {MIN_PRINT_PT}pt "
              f"(삽입폭 {insert_width_in}in). 열 수를 줄이거나 삽입폭을 늘리세요.", file=sys.stderr)
    return path


def draw_structure(smiles, filename, label="", size=(500, 380), insert_width_in=3.0):
    """SMILES 하나를 구조식 + 아래 라벨 PNG로 저장하고 경로를 돌려준다."""
    font = _load_font(LABEL_FONT_PX)
    lines = _normalize(label)
    mol_img = _mol_image(_mol_from_smiles(smiles), size)
    cap_h = _caption_height(lines, font) if label else 0
    canvas = Image.new("RGB", (size[0], size[1] + cap_h), "white")
    canvas.paste(mol_img, (0, 0))
    if label:
        _draw_caption(canvas, lines, font, (0, size[1], size[0], cap_h))
    return _save(canvas, filename, insert_width_in)


def draw_grid(items, filename, mols_per_row=3, sub_img_size=(350, 280), insert_width_in=6.0):
    """[(라벨, SMILES), ...]를 격자 한 장(PNG)으로 저장하고 경로를 돌려준다."""
    if not items:
        raise ValueError("items가 비어 있음")
    font = _load_font(LABEL_FONT_PX)
    labels = [_normalize(label) for label, _ in items]
    mols = [_mol_from_smiles(smiles) for _, smiles in items]
    n_cols = min(mols_per_row, len(mols))
    n_rows = (len(mols) + n_cols - 1) // n_cols
    w, h = sub_img_size
    cap_h = max(_caption_height(lines, font) for lines in labels)
    cell_h = h + cap_h
    canvas = Image.new("RGB", (w * n_cols, cell_h * n_rows), "white")
    for i, (mol, lines) in enumerate(zip(mols, labels)):
        x, y = (i % n_cols) * w, (i // n_cols) * cell_h
        canvas.paste(_mol_image(mol, sub_img_size), (x, y))
        _draw_caption(canvas, lines, font, (x, y + h, w, cap_h))
    return _save(canvas, filename, insert_width_in)


if __name__ == "__main__":
    out = Path(__file__).parent / "examples"
    print(draw_structure("CC(=O)Oc1ccccc1C(=O)O", out / "aspirin.png", "Aspirin\n(아스피린)"))
    print(draw_grid(
        [
            ("Aspirin\n(아스피린)", "CC(=O)Oc1ccccc1C(=O)O"),
            ("Ibuprofen\n(이부프로펜)", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
            ("(S)-Naproxen\n(나프록센)", "COc1ccc2cc(ccc2c1)[C@H](C)C(=O)O"),
            ("Acetaminophen\n(아세트아미노펜)", "CC(=O)Nc1ccc(O)cc1"),
        ],
        out / "analgesics_grid.png",
        mols_per_row=2,
    ))
