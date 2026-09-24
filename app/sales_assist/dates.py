"""「来週金曜」「10月16日」などの期限表現を、商談日を基準に具体的な日付へ変換する。"""
import re
import unicodedata
from datetime import date, timedelta

WEEKDAYS = "月火水木金土日"


def resolve_due(expr: str | None, base: date) -> date | None:
    """期限表現を日付に変換する。変換できない場合は None（画面では「要確認」と表示）。"""
    if not expr:
        return None
    s = unicodedata.normalize("NFKC", str(expr)).strip()

    m = re.search(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})", s)
    if m:
        return _safe_date(int(m[1]), int(m[2]), int(m[3]))

    m = re.search(r"(\d{1,2})[/月](\d{1,2})日?", s)
    if m:
        d = _safe_date(base.year, int(m[1]), int(m[2]))
        # 商談日より半年以上前になる場合は翌年とみなす（10月の商談で「1月15日」など）
        if d and (base - d).days > 180:
            d = _safe_date(base.year + 1, int(m[1]), int(m[2]))
        return d

    if "明後日" in s:
        return base + timedelta(days=2)
    if "明日" in s:
        return base + timedelta(days=1)
    if "今日" in s or "本日" in s:
        return base

    m = re.search(r"(\d+)\s*日後", s)
    if m:
        return base + timedelta(days=int(m[1]))

    m = re.search(r"(再来週|来週|今週)\s*の?\s*([月火水木金土日])曜?", s)
    if m:
        weeks = {"今週": 0, "来週": 1, "再来週": 2}[m[1]]
        monday = base - timedelta(days=base.weekday())
        return monday + timedelta(weeks=weeks, days=WEEKDAYS.index(m[2]))

    m = re.search(r"(来週|今週)中", s)
    if m:
        monday = base - timedelta(days=base.weekday())
        return monday + timedelta(weeks=1 if m[1] == "来週" else 0, days=4)

    return None


def format_date(d: date | None) -> str:
    return f"{d.year}/{d.month:02d}/{d.day:02d}（{WEEKDAYS[d.weekday()]}）" if d else "要確認"


def _safe_date(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None
