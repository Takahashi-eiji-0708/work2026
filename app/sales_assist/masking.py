"""AI に送る前のマスキングと、出力後の復元。

- 電話番号・メールアドレスは自動で検出して置き換える（復元しない＝AIの出力にも残さない）
- 登録した固有名詞（社名・人名など）は記号に置き換え、出力後に元の名前へ戻す
- 置換表はアプリの中だけで使い、AI には送らない
"""
import re
import unicodedata
from dataclasses import dataclass, field

PHONE_RE = re.compile(r"(?<!\d)0\d{1,4}[-(（]?\d{1,4}[-)）]?\d{3,4}(?!\d)")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

CATEGORY_LABELS = {"COMPANY": "会社名", "PERSON": "人名", "OTHER": "その他"}


@dataclass
class MaskResult:
    text: str
    mapping: dict = field(default_factory=dict)  # 記号 → 元の語（復元対象のみ）
    counts: dict = field(default_factory=dict)   # 種類 → 件数（画面表示用）


def normalize(text: str) -> str:
    """全角の英数字と「＠．－＿＋」を半角にそろえ、数字の間のハイフン類を「-」に統一する。

    文章全体を NFKC 正規化すると「：」「（」なども半角になり議事録の見た目が変わるため、
    電話番号・メールアドレスの検出に必要な文字だけを変換する。
    """
    text = "".join(
        unicodedata.normalize("NFKC", ch) if ch.isalnum() and ord(ch) >= 0xFF00 or ch in "＠．－＿＋" else ch
        for ch in text
    )
    return re.sub(r"(?<=\d)[‐‑‒–—―−ー－](?=\d)", "-", text)


def mask(text: str, terms: list[tuple[str, str]] | None = None) -> MaskResult:
    """text をマスキングする。terms は (語, 種類) のリスト。種類は COMPANY / PERSON / OTHER。"""
    text = normalize(text)
    counts: dict[str, int] = {}

    def _count(kind: str, n: int):
        if n:
            counts[kind] = counts.get(kind, 0) + n

    text, n = EMAIL_RE.subn("[メールアドレス]", text)
    _count("メールアドレス", n)
    text, n = PHONE_RE.subn("[電話番号]", text)
    _count("電話番号", n)

    mapping: dict[str, str] = {}
    seq: dict[str, int] = {}
    # 長い語から置換する（「みなと精機」より先に「株式会社みなと精機」を置換するため）
    for term, kind in sorted(terms or [], key=lambda t: len(t[0]), reverse=True):
        term = normalize(term).strip()
        if not term or term not in text:
            continue
        kind = kind if kind in CATEGORY_LABELS else "OTHER"
        seq[kind] = seq.get(kind, 0) + 1
        token = f"[{kind}_{seq[kind]}]"
        _count(CATEGORY_LABELS[kind], text.count(term))
        text = text.replace(term, token)
        mapping[token] = term
    return MaskResult(text, mapping, counts)


def unmask(text: str, mapping: dict) -> str:
    """記号を元の語に戻す。"""
    for token, term in mapping.items():
        text = text.replace(token, term)
    return text


def unmask_obj(obj, mapping: dict):
    """dict / list / str を再帰的に復元する（議事録の JSON 用）。"""
    if isinstance(obj, str):
        return unmask(obj, mapping)
    if isinstance(obj, list):
        return [unmask_obj(v, mapping) for v in obj]
    if isinstance(obj, dict):
        return {k: unmask_obj(v, mapping) for k, v in obj.items()}
    return obj
