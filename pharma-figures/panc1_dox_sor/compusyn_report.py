"""CompuSyn Report(HTML 내보내기)에서 그래프용 수치를 읽는다.

    from compusyn_report import load_report
    r = load_report("compusyn_report.html")
    r["params"]["SOR"]        # {"Dm": 0.27714, "m": 1.15661, "r": 0.79314}
    r["dose_effect"]["DOX"]   # [(dose, Fa), ...]
    r["ci_curve"]             # [(Fa, CI, total dose), ...]
    r["ci_points"]            # [(total dose, Fa, CI), ...]
    r["dri_curve"]            # [(Fa, dose SOR, dose DOX, DRI SOR, DRI DOX), ...]
    r["dri_points"]           # 실측점 기준, 형식은 dri_curve와 같음
    r["ed"][0.5]              # {"CI", "Dx": {"SOR", "DOX"}, "combo": {"SOR", "DOX"}}
"""

import re
from pathlib import Path


def _num(cell):
    cell = cell.replace("&nbsp;", "").replace("+", "").strip()
    return float(cell) if cell else None


def _rows_after(html, label):
    """label 다음에 오는 첫 번째 <table>의 숫자 행 목록."""
    start = html.index(label)
    table = re.search(r"<table.*?</table>", html[start:], re.S).group(0)
    rows = []
    for row in re.split(r"<tr>", table)[1:]:
        cells = re.findall(r"<td>([^<]*)", row)
        if not cells or "<th" in row.split("<td>")[0]:
            continue
        rows.append(tuple(_num(c) for c in cells))
    return rows


def _params_after(html, label):
    start = html.index(label)
    block = html[start:start + 3000]
    get = lambda key: float(re.search(rf"<th align=left>{key}:\s*<td>\s*([-\d.E]+)", block).group(1))
    return {"Dm": get("Dm"), "m": get("m"), "r": get("r")}


def load_report(path):
    html = Path(path).read_text(encoding="latin-1")
    labels = {
        "SOR": "Data for Drug: SOR",
        "DOX": "Data for Drug: DOX",
        "DOX+SOR": "Data for Drug Combo: DOXSOR",
    }
    report = {
        "params": {k: _params_after(html, v) for k, v in labels.items()},
        "dose_effect": {k: _rows_after(html, v) for k, v in labels.items()},
        "ci_curve": _rows_after(html, "CI Data for Drug Combo"),
        "ci_points": _rows_after(html, "CI values for actual experimental points"),
        "dri_curve": _rows_after(html, "DRI Data for Drug Combo"),
        "dri_points": _rows_after(html, "DRI values calculated at experimental points"),
        "ed": {},
    }
    for m in re.finditer(r"Data for Fa = ([\d.]+)", html):
        table = re.search(r"<table.*?</table>", html[m.end():], re.S).group(0)
        # 열 순서: 약물 | CI | Dose SOR | Dose DOX (단독 행은 해당 칸만 채워짐)
        cols = {}
        for row in re.split(r"<tr>", table)[1:]:
            cells = re.findall(r"<td>([^<]*)", row)
            if cells:
                cols[cells[0].strip()] = [_num(c) for c in cells[1:]] + [None] * 3
        report["ed"][float(m.group(1))] = {
            "CI": cols["DOXSOR"][0],
            "Dx": {"SOR": cols["SOR"][1], "DOX": cols["DOX"][2]},
            "combo": {"SOR": cols["DOXSOR"][1], "DOX": cols["DOXSOR"][2]},
        }
    return report


if __name__ == "__main__":
    import json
    r = load_report(Path(__file__).with_name("compusyn_report.html"))
    print(json.dumps({k: (v if k in ("params", "ed") else len(v) if isinstance(v, list)
                          else {kk: len(vv) for kk, vv in v.items()}) for k, v in r.items()},
                     indent=1, default=str))
