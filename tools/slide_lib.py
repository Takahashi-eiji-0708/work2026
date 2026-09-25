"""ELI PowerPoint テンプレート（A4横）にスライドを組み立てるための部品。

テンプレートのスライドはすべて取り除き、レイアウト（表紙・章扉・コンテンツ）を参照する
新しいスライドを XML で書き出す。ページ番号は入れず、著作権フッターは必ず入れる。
"""
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
FONT = ('<a:latin typeface="Noto Sans JP"/><a:ea typeface="Noto Sans JP"/>'
        '<a:cs typeface="Noto Sans JP"/><a:sym typeface="Noto Sans JP"/>')
TABLE_STYLE = "{7DF18680-E054-41AD-8BC1-D1AEF772440D}"
COPYRIGHT = "© Edifist Learning Inc. All rights reserved."

# 配色（テンプレートの紺・青を基調に、注意喚起だけオレンジ）
NAVY, BLUE, LIGHT, PALE, TEXT, GRAY, ORANGE, ORANGE_PALE, WHITE = (
    "004D88", "0078C8", "DCEBF7", "F2F7FC", "333333", "666666", "E8710A", "FDEBDC", "FFFFFF")

# 本文エリア（タイトル帯の下〜フッター帯の上）
X0, Y0, W, BOTTOM = 330000, 1000000, 9246000, 6380000

LAYOUT = {"cover": 1, "section": 2, "content": 3}


# --------------------------------------------------------------------- テキスト
def run(text, size=1600, bold=False, color=TEXT, italic=False):
    return (f'<a:r><a:rPr lang="ja-JP" altLang="en-US" sz="{size}" b="{int(bold)}" i="{int(italic)}" dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>{FONT}</a:rPr>'
            f'<a:t>{escape(text)}</a:t></a:r>')


def runs(text, size=1600, bold=False, color=TEXT, accent=None):
    """**太字** 記法に対応した run の列。accent を指定すると太字部分をその色にする。"""
    out = []
    for tok in re.split(r"(\*\*[^*]+\*\*)", text):
        if not tok:
            continue
        if tok.startswith("**"):
            out.append(run(tok[2:-2], size, True, accent or color))
        else:
            out.append(run(tok, size, bold, color))
    return "".join(out)


def para(text="", size=1600, bold=False, color=TEXT, align="l", bullet=None, level=0,
         space_before=0, space_after=0, line=None, accent=None, line_pts=None):
    """bullet: None / "dot" / "num" / "check" / 任意の1文字"""
    ppr = [f'algn="{align}"']
    inner = ""
    if line_pts:
        inner += f'<a:lnSpc><a:spcPts val="{line_pts}"/></a:lnSpc>'
    elif line:
        inner += f'<a:lnSpc><a:spcPct val="{line}"/></a:lnSpc>'
    inner += f'<a:spcBef><a:spcPts val="{space_before}"/></a:spcBef><a:spcAft><a:spcPts val="{space_after}"/></a:spcAft>'
    if bullet:
        indent = 400000 if bullet == "num" else 228600
        ppr += [f'marL="{indent * (level + 1)}"', f'indent="-{indent}"']
        if bullet == "num":
            inner += f'<a:buClr><a:srgbClr val="{BLUE}"/></a:buClr><a:buFont typeface="+mj-lt"/><a:buAutoNum type="arabicPeriod"/>'
        else:
            ch = {"dot": "●", "check": "✓"}.get(bullet, bullet)
            inner += (f'<a:buClr><a:srgbClr val="{BLUE}"/></a:buClr><a:buSzPct val="80000"/>'
                      f'<a:buFont typeface="Noto Sans JP"/><a:buChar char="{escape(ch)}"/>')
    else:
        ppr += ['marL="0"', 'indent="0"']
        inner += "<a:buNone/>"
    body = runs(text, size, bold, color, accent) if text else ""
    return (f'<a:p><a:pPr {" ".join(ppr)}>{inner}</a:pPr>{body}'
            f'<a:endParaRPr lang="ja-JP" altLang="en-US" sz="{size}" dirty="0">{FONT}</a:endParaRPr></a:p>')


def ps(items, **kw):
    """文字列または (文字列, dict) のリストを段落の XML にする。"""
    out = []
    for it in items:
        if isinstance(it, tuple):
            text, opts = it
            out.append(para(text, **{**kw, **opts}))
        else:
            out.append(para(it, **kw))
    return "".join(out)


# --------------------------------------------------------------------- 図形
class Slide:
    def __init__(self, kind, title=""):
        self.kind = kind
        self.title = title
        self.shapes = []
        self._id = 10

    def next_id(self):
        self._id += 1
        return self._id

    def box(self, x, y, w, h, paras="", fill=None, line=None, prst="rect", anchor="t",
            inset=(91440, 45720, 91440, 45720), line_w=12700, shadow=False, adj=None, rot=0):
        sid = self.next_id()
        fill_xml = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
        line_xml = (f'<a:ln w="{line_w}"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
                    if line else "<a:ln><a:noFill/></a:ln>")
        av = "".join(f'<a:gd name="{k}" fmla="val {v}"/>' for k, v in (adj or {}).items())
        eff = ('<a:effectLst><a:outerShdw blurRad="50800" dist="19050" dir="5400000" algn="t" rotWithShape="0">'
               '<a:srgbClr val="000000"><a:alpha val="18000"/></a:srgbClr></a:outerShdw></a:effectLst>') if shadow else ""
        l, t, r, b = inset
        rot_attr = f' rot="{int(rot * 60000)}"' if rot else ""
        txbox = ' txBox="1"' if not fill and not line and prst == "rect" else ""
        self.shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Shape {sid}"/><p:cNvSpPr{txbox}/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm{rot_attr}><a:off x="{int(x)}" y="{int(y)}"/>'
            f'<a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="{prst}"><a:avLst>{av}</a:avLst></a:prstGeom>{fill_xml}{line_xml}{eff}</p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="{l}" tIns="{t}" rIns="{r}" bIns="{b}" anchor="{anchor}" rtlCol="0">'
            f'<a:noAutofit/></a:bodyPr><a:lstStyle/>{paras or para("")}</p:txBody></p:sp>')

    def body_placeholder(self, x, y, w, h, paras):
        """レイアウトの本文プレースホルダー（idx=1）を位置指定して使う（目次用）。"""
        sid = self.next_id()
        self.shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Body {sid}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph idx="1"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/>'
            f'</a:xfrm></p:spPr><p:txBody><a:bodyPr><a:noAutofit/></a:bodyPr><a:lstStyle/>{paras}</p:txBody></p:sp>')

    def circle_num(self, x, y, d, label, fill=BLUE, size=1400):
        self.box(x, y, d, d, para(str(label), size=size, bold=True, color=WHITE, align="ctr"),
                 fill=fill, prst="ellipse", anchor="ctr", inset=(0, 0, 0, 0))

    def text(self, x, y, w, h, paras, anchor="t"):
        self.box(x, y, w, h, paras, anchor=anchor, inset=(0, 0, 0, 0))

    def table(self, x, y, col_widths, rows, row_h=420000, size=1200, header_size=None,
              fills=None, bold_cols=(), aligns=None, header=True):
        """rows[0] がヘッダー。fills は {(行, 列) or 行: 色}。"""
        sid = self.next_id()
        fills = fills or {}
        grid = "".join(f'<a:gridCol w="{int(cw)}"/>' for cw in col_widths)
        trs = []
        for i, row in enumerate(rows):
            tcs = []
            for j, cell in enumerate(row):
                is_head = header and i == 0
                color = WHITE if is_head else TEXT
                lines = str(cell).split("\n")
                align = (aligns[j] if aligns else "l")
                p_xml = "".join(
                    para(ln, size=(header_size or size) if is_head else size, bold=is_head or j in bold_cols,
                         color=color, align=align) for ln in lines)
                fill = fills.get((i, j), fills.get(i))
                fill_xml = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else ""
                tcs.append(f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>{p_xml}</a:txBody>'
                           f'<a:tcPr marL="72000" marR="72000" marT="36000" marB="36000" anchor="ctr">{fill_xml}</a:tcPr></a:tc>')
            h = row_h[i] if isinstance(row_h, (list, tuple)) else row_h
            trs.append(f'<a:tr h="{int(h)}">{"".join(tcs)}</a:tr>')
        total_h = sum(row_h) if isinstance(row_h, (list, tuple)) else row_h * len(rows)
        self.shapes.append(
            f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{sid}" name="Table {sid}"/>'
            f'<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>'
            f'<p:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(sum(col_widths))}" cy="{int(total_h)}"/></p:xfrm>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
            f'<a:tbl><a:tblPr firstRow="{int(header)}" bandRow="1"><a:tableStyleId>{TABLE_STYLE}</a:tableStyleId></a:tblPr>'
            f'<a:tblGrid>{grid}</a:tblGrid>{"".join(trs)}</a:tbl></a:graphicData></a:graphic></p:graphicFrame>')

    # ----------------------------------------------------------------- 出力
    def xml(self):
        ids = iter(range(2, 10))
        ph = []
        if self.kind == "cover":
            title, sub = self.title
            tparas = "".join(para(t, size=2700, bold=True, color=NAVY, line=110000) for t in title.split("\n"))
            ph.append(_ph(next(ids), "Title", '<p:ph type="ctrTitle"/>', tparas, autofit=True))
            ph.append(_ph(next(ids), "Subtitle", '<p:ph type="subTitle" idx="1"/>',
                          "".join(para(t, size=1600, color=NAVY) for t in sub.split("\n"))))
        else:
            ph.append(_ph(next(ids), "Title", '<p:ph type="title"/>', para_title(self.title, self.kind), autofit=True))
            if self.kind == "section":
                ph.append(_ph(next(ids), "Body", '<p:ph type="body" idx="1"/>', para("")))
            ph.append(_ph(next(ids), "Footer", '<p:ph type="ftr" sz="quarter" idx="10"/>',
                          f'<a:p><a:r><a:rPr lang="en-US" altLang="ja-JP"/><a:t>{escape(COPYRIGHT)}</a:t></a:r></a:p>'))
        tree = "".join(ph) + "".join(self.shapes)
        return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld {NS}><p:cSld><p:spTree>'
                '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
                f'{tree}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


def para_title(text, kind):
    """タイトルはレイアウトの色・サイズを継承し、フォントだけ Noto Sans JP を指定する。"""
    return (f'<a:p><a:r><a:rPr lang="ja-JP" altLang="en-US" cap="none" dirty="0">{FONT}</a:rPr>'
            f'<a:t>{escape(text)}</a:t></a:r></a:p>')


def _ph(sid, name, ph, paras, autofit=False):
    fit = "<a:normAutofit/>" if autofit else ""
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr>{ph}</p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr>{fit}</a:bodyPr><a:lstStyle/>{paras}</p:txBody></p:sp>')


# --------------------------------------------------------------------- パッケージ
def build(template: Path, slides: list[Slide], out: Path):
    work = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(template) as z:
        z.extractall(work)
    ppt = work / "ppt"
    # 既存のスライドをすべて取り除く
    shutil.rmtree(ppt / "slides")
    (ppt / "slides" / "_rels").mkdir(parents=True)
    ct_path = work / "[Content_Types].xml"
    ct = re.sub(r'<Override PartName="/ppt/slides/slide\d+\.xml"[^>]*/>', "", ct_path.read_text(encoding="utf-8"))
    rels_path = ppt / "_rels" / "presentation.xml.rels"
    rels = re.sub(r'<Relationship Id="[^"]+" Type="[^"]+/slide" Target="slides/slide\d+\.xml"/>', "",
                  rels_path.read_text(encoding="utf-8"))
    pres_path = ppt / "presentation.xml"
    pres = pres_path.read_text(encoding="utf-8")

    overrides, new_rels, sld_ids = [], [], []
    for i, s in enumerate(slides, 1):
        (ppt / "slides" / f"slide{i}.xml").write_text(s.xml(), encoding="utf-8")
        (ppt / "slides" / "_rels" / f"slide{i}.xml.rels").write_text(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" '
            f'Target="../slideLayouts/slideLayout{LAYOUT[s.kind]}.xml"/></Relationships>', encoding="utf-8")
        overrides.append(f'<Override PartName="/ppt/slides/slide{i}.xml" '
                         'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
        new_rels.append(f'<Relationship Id="rIdS{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
                        f'Target="slides/slide{i}.xml"/>')
        sld_ids.append(f'<p:sldId id="{300 + i}" r:id="rIdS{i}"/>')
    ct_path.write_text(ct.replace("</Types>", "".join(overrides) + "</Types>"), encoding="utf-8")
    rels_path.write_text(rels.replace("</Relationships>", "".join(new_rels) + "</Relationships>"), encoding="utf-8")
    pres_path.write_text(re.sub(r"<p:sldIdLst>.*?</p:sldIdLst>", f"<p:sldIdLst>{''.join(sld_ids)}</p:sldIdLst>", pres),
                         encoding="utf-8")
    # 旧スライドの編集履歴は不要なので削除する
    for part in ("changesInfos", "revisionInfo.xml"):
        p = ppt / part
        if p.exists():
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    rels_path.write_text(re.sub(r'<Relationship Id="[^"]+" Type="[^"]+/(revisionInfo|changesInfo)" Target="(revisionInfo.xml|changesInfos/[^"]+)"/>', "",
                                rels_path.read_text(encoding="utf-8")), encoding="utf-8")
    ct_path.write_text(re.sub(r'<Override PartName="/ppt/(revisionInfo\.xml|changesInfos/[^"]+)"[^>]*/>', "",
                              ct_path.read_text(encoding="utf-8")), encoding="utf-8")

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml を先頭に置く
        z.write(ct_path, "[Content_Types].xml")
        for f in sorted(work.rglob("*")):
            if f.is_file() and f != ct_path:
                z.write(f, f.relative_to(work).as_posix())
    shutil.rmtree(work)
