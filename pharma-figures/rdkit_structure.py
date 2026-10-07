"""RDKit으로 약물 화학 구조식을 그리는 도우미.

사용 예:
    from rdkit_structure import draw_structure, draw_grid

    draw_structure("CC(=O)Oc1ccccc1C(=O)O", "aspirin.png", "Aspirin (아스피린)")
    draw_grid(
        [("Ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
         ("Naproxen", "COc1ccc2cc(ccc2c1)C(C)C(=O)O")],
        "nsaids.png",
        mols_per_row=2,
    )

라벨은 RDKit legend 자리(구조식 아래)에 들어간다. RDKit 자체 글꼴은 한글을
□로 그리므로, 한글이 섞인 라벨은 같은 자리에 Pillow(PNG) 또는 SVG <text>로
시스템 한글 폰트(맑은 고딕, 애플고딕, 나눔/Noto CJK)를 써서 얹는다.
출력 형식은 파일 확장자로 정한다(.png 또는 .svg).
"""

import io
import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

# 한글 라벨용 폰트 후보 (먼저 찾은 것을 사용)
_KOREAN_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\malgun.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/AppleGothic.ttf",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
]

_SVG_FONT_FAMILY = "Malgun Gothic, Apple SD Gothic Neo, NanumGothic, Noto Sans CJK KR, sans-serif"


def _find_korean_font():
    env_font = os.environ.get("PHARMA_FIG_FONT")
    if env_font and Path(env_font).exists():
        return env_font
    for path in _KOREAN_FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def _mol_from_smiles(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"SMILES를 해석할 수 없음: {smiles!r}")
    AllChem.Compute2DCoords(mol)
    return mol


def _apply_options(drawer):
    opts = drawer.drawOptions()
    opts.addStereoAnnotation = True
    opts.legendFontSize = 20
    opts.legendFraction = 0.12
    opts.padding = 0.08


def _rdkit_legends(labels):
    # RDKit의 글꼴 렌더러는 한글 같은 비ASCII 문자를 □로 그리므로, 그런 라벨은
    # 공백 legend로 자리만 잡아두고 실제 글자는 _overlay_labels에서 얹는다.
    return [label if label.isascii() else " " for label in labels]


def _overlay_labels(data, labels, n_cols, panel_size, is_svg):
    pending = [(i, label) for i, label in enumerate(labels) if not label.isascii()]
    if not pending:
        return data
    w, h = panel_size
    font_size = 20
    positions = [((i % n_cols) * w + w / 2, (i // n_cols) * h + h * (1 - 0.12 / 2))
                 for i, _ in pending]

    if is_svg:
        texts = "".join(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="{_SVG_FONT_FAMILY}" font-size="{font_size}">{escape(label)}</text>\n'
            for (_, label), (x, y) in zip(pending, positions)
        )
        return data.replace("</svg>", texts + "</svg>")

    font_path = _find_korean_font()
    if font_path is None:
        print("경고: 한글 폰트를 찾지 못해 라벨이 깨질 수 있음. "
              "PHARMA_FIG_FONT 환경변수에 .ttf 경로를 지정하세요.", file=sys.stderr)
        font = ImageFont.load_default(size=font_size)
    else:
        font = ImageFont.truetype(font_path, font_size)
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    draw = ImageDraw.Draw(img)
    for (_, label), (x, y) in zip(pending, positions):
        fitted = font
        # 패널 폭을 넘는 긴 라벨은 글자 크기를 줄여 맞춘다
        if font_path and draw.textlength(label, font=font) > w * 0.95:
            fitted = ImageFont.truetype(font_path, int(font_size * w * 0.95 / draw.textlength(label, font=font)))
        draw.text((x, y), label, font=fitted, fill="black", anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _render(filename, size, mols, labels, n_cols=1, panel_size=None):
    path = Path(filename)
    is_svg = path.suffix.lower() == ".svg"
    panel_size = panel_size or size
    drawer_cls = rdMolDraw2D.MolDraw2DSVG if is_svg else rdMolDraw2D.MolDraw2DCairo
    if len(mols) == 1:
        drawer = drawer_cls(*size)
    else:
        drawer = drawer_cls(*size, *panel_size)
    _apply_options(drawer)
    legends = _rdkit_legends(labels)
    if len(mols) == 1:
        drawer.DrawMolecule(mols[0], legend=legends[0])
    else:
        drawer.DrawMolecules(mols, legends=legends)
    drawer.FinishDrawing()
    data = _overlay_labels(drawer.GetDrawingText(), labels, n_cols, panel_size, is_svg)

    path.parent.mkdir(parents=True, exist_ok=True)
    if is_svg:
        path.write_text(data, encoding="utf-8")
    else:
        path.write_bytes(data)
    return path


def draw_structure(smiles, filename, label="", size=(500, 400)):
    """SMILES 하나를 구조식 그림으로 저장하고 저장 경로를 돌려준다."""
    return _render(filename, size, [_mol_from_smiles(smiles)], [label])


def draw_grid(items, filename, mols_per_row=3, sub_img_size=(350, 300)):
    """[(라벨, SMILES), ...] 목록을 격자 한 장으로 저장하고 저장 경로를 돌려준다."""
    if not items:
        raise ValueError("items가 비어 있음")
    labels = [label for label, _ in items]
    mols = [_mol_from_smiles(smiles) for _, smiles in items]
    n_cols = min(mols_per_row, len(mols))
    n_rows = (len(mols) + n_cols - 1) // n_cols
    w, h = sub_img_size
    return _render(filename, (w * n_cols, h * n_rows), mols, labels, n_cols, sub_img_size)


if __name__ == "__main__":
    out = Path(__file__).parent / "examples"
    print(draw_structure("CC(=O)Oc1ccccc1C(=O)O", out / "aspirin.png", "Aspirin (아스피린)"))
    print(draw_grid(
        [
            ("Aspirin", "CC(=O)Oc1ccccc1C(=O)O"),
            ("Ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
            ("Naproxen", "COc1ccc2cc(ccc2c1)[C@H](C)C(=O)O"),
            ("Acetaminophen (아세트아미노펜)", "CC(=O)Nc1ccc(O)cc1"),
        ],
        out / "analgesics_grid.png",
        mols_per_row=2,
    ))
