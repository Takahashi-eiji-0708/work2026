"""docs/*.md を配布用の Word ファイル（docs/word/*.docx）に変換する。

対応する記法：見出し・段落・箇条書き・番号付きリスト・チェックボックス・表・コードブロック・引用・区切り線
    python tools/md_to_docx.py
"""
import re
from pathlib import Path

from docx.enum.text import WD_BREAK
from docx.shared import Pt, RGBColor

from docx_helpers import add_inline, bullet, heading, new_document, para, shade, table

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs"
DST = SRC / "word"


def convert(md_path: Path, out_path: Path):
    doc = new_document()
    lines = md_path.read_text(encoding="utf-8").splitlines()
    i = 0
    first_h1 = True
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("```"):
            i += 1
            block = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            t = doc.add_table(rows=1, cols=1)
            t.style = "Table Grid"
            cell = t.cell(0, 0)
            shade(cell, "F2F2F2")
            p = cell.paragraphs[0]
            for k, b in enumerate(block):
                run = p.add_run(b)
                run.font.name = "Consolas"
                run.font.size = Pt(9)
                rpr = run._element.get_or_add_rPr()
                rpr.rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia", "游ゴシック")
                if k < len(block) - 1:
                    run.add_break(WD_BREAK.LINE)
            doc.add_paragraph()
        elif s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    rows.append([c.replace("<br>", "\n") for c in cells])
                i += 1
            width = max(len(r) for r in rows)
            rows = [r + [""] * (width - len(r)) for r in rows]
            table(doc, rows)
            continue
        elif s.startswith("#"):
            level = len(s) - len(s.lstrip("#"))
            text = s[level:].strip()
            if level == 1 and first_h1:
                para(doc, text, size=18, bold=True, color=RGBColor(0x00, 0x4D, 0x88))
                first_h1 = False
            else:
                heading(doc, text, min(level if level > 1 else 1, 3))
        elif s.startswith(">"):
            p = para(doc)
            add_inline(p, s.lstrip("> ").strip() or " ", size=9.5, color=RGBColor(0x40, 0x40, 0x40))
            p.paragraph_format.left_indent = Pt(12)
        elif re.match(r"^- \[[ x]\] ", s):
            p = para(doc)
            add_inline(p, "☐ " + s[6:])
        elif s.startswith("- ") or s.startswith("* "):
            b = bullet(doc, s[2:])
            if line.startswith("  "):
                b.paragraph_format.left_indent = Pt(36)
        elif re.match(r"^\d+\. ", s):
            p = para(doc)
            add_inline(p, s)
            if line.startswith("  "):
                p.paragraph_format.left_indent = Pt(18)
        elif s == "---":
            pass
        elif s:
            para(doc, s)
        i += 1
    doc.save(out_path)


def main():
    DST.mkdir(exist_ok=True)
    for md in sorted(SRC.glob("*.md")):
        out = DST / (md.stem + ".docx")
        convert(md, out)
        print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
