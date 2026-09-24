"""画面から呼び出す処理：マスキング → LLM → 検証 → 日付の具体化 → 復元。"""
import csv
import io
import json
import logging
from dataclasses import dataclass
from datetime import date

from .dates import format_date, resolve_due
from .llm import LLMClient, LLMFormatError, extract_json
from .masking import MaskResult, mask, unmask_obj
from .prompts import EMAIL_SYSTEM, EMAIL_USER, MINUTES_SYSTEM, MINUTES_USER

# 商談の本文はログに出さない（件数や文字数などのメタ情報だけを記録する）
logger = logging.getLogger("sales_assist")

MINUTES_KEYS = ("summary", "background", "requirements", "concerns", "decisions", "actions")


@dataclass
class MinutesResult:
    minutes: dict          # 画面表示用（名前を復元済み）
    actions: list[dict]    # DB 保存用
    masked_prompt: str     # AI に送った内容（確認用）


def build_minutes_prompt(meeting: dict, terms: list[tuple[str, str]]) -> tuple[str, MaskResult]:
    """AI に送る内容を組み立てる。顧客名・出席者も含めてマスキングする。"""
    raw = MINUTES_USER.format(
        meeting_date=meeting["meeting_date"], customer=meeting["customer"],
        attendees=meeting.get("attendees", ""), memo=meeting["memo"],
    )
    result = mask(raw, terms)
    return result.text, result


def generate_minutes(llm: LLMClient, meeting: dict, terms: list[tuple[str, str]], retries: int = 1) -> MinutesResult:
    prompt, masked = build_minutes_prompt(meeting, terms)
    logger.info("generate_minutes meeting_id=%s chars=%d masked=%s", meeting.get("id"), len(prompt), masked.counts)
    data = _complete_json(llm, MINUTES_SYSTEM, prompt, retries)
    data = _normalize_minutes(data)

    base = date.fromisoformat(meeting["meeting_date"])
    for a in data["actions"]:
        d = resolve_due(a.get("due"), base)
        a["due_date"] = d.isoformat() if d else None
        a["due_label"] = format_date(d) if d else f"要確認（{a['due']}）" if a.get("due") else "要確認"

    minutes = unmask_obj(data, masked.mapping)
    actions = [
        {"owner": a.get("owner", ""), "task": a.get("task", ""), "due_text": a.get("due", ""), "due_date": a["due_date"]}
        for a in minutes["actions"]
    ]
    return MinutesResult(minutes, actions, prompt)


def draft_email(llm: LLMClient, minutes: dict, terms: list[tuple[str, str]], recipient: str, tone: str,
                sender: str, retries: int = 1) -> dict:
    """議事録（復元済み）から、再度マスキングしてメールを下書きする。"""
    raw = EMAIL_USER.format(recipient=recipient, tone=tone, sender=sender,
                            minutes=json.dumps(minutes, ensure_ascii=False, indent=2))
    masked = mask(raw, terms)
    logger.info("draft_email recipient=%s chars=%d", recipient, len(masked.text))
    data = _complete_json(llm, EMAIL_SYSTEM, masked.text, retries)
    email = {"subject": str(data.get("subject", "")), "body": str(data.get("body", ""))}
    return unmask_obj(email, masked.mapping)


def minutes_to_text(m: dict) -> str:
    """議事録を Word などに貼り付けやすいテキストにする。"""
    lines = ["■ 要約", m.get("summary", ""), "", "■ 背景・目的"]
    lines += [f"・{x}" for x in m.get("background", [])]
    lines += ["", "■ 確認した要件"] + [f"・{r.get('item')}：{r.get('detail')}" for r in m.get("requirements", [])]
    lines += ["", "■ 懸念・課題"] + [f"・{x}" for x in m.get("concerns", [])]
    lines += ["", "■ 決定事項"] + [f"・{x}" for x in m.get("decisions", [])]
    lines += ["", "■ 次回までのアクション"]
    lines += [f"・{a.get('owner')}：{a.get('task')}（期限：{a.get('due_label', '要確認')}）" for a in m.get("actions", [])]
    return "\n".join(lines)


def actions_to_csv(actions: list[dict]) -> bytes:
    """行動リストを CSV にする。Excel で文字化けしないよう BOM 付き UTF-8 で出力する。"""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(["顧客", "商談日", "担当", "内容", "期限", "期限（元の表現）", "状態"])
    for a in actions:
        w.writerow([a.get("customer", ""), a.get("meeting_date", ""), a["owner"], a["task"],
                    a.get("due_date") or "要確認", a.get("due_text", ""), a["status"]])
    return buf.getvalue().encode("utf-8-sig")


def is_overdue(action: dict, today: date) -> bool:
    return bool(action.get("due_date")) and action["status"] != "完了" and date.fromisoformat(action["due_date"]) < today


def _complete_json(llm: LLMClient, system: str, user: str, retries: int) -> dict:
    last_error = None
    for attempt in range(retries + 1):
        text = llm.complete(system, user)
        try:
            return extract_json(text)
        except LLMFormatError as e:
            last_error = e
            logger.warning("LLM output format error (attempt %d): %s", attempt + 1, e)
    raise last_error


def _normalize_minutes(data: dict) -> dict:
    """足りない項目を補い、型をそろえる（LLM の出力は形が崩れることがあるため）。"""
    out = {k: data.get(k) for k in MINUTES_KEYS}
    out["summary"] = str(out["summary"] or "")
    for k in ("background", "concerns", "decisions"):
        v = out[k] or []
        out[k] = [str(x) for x in (v if isinstance(v, list) else [v])]
    out["requirements"] = [r for r in (out["requirements"] or []) if isinstance(r, dict)]
    out["actions"] = [
        {"owner": str(a.get("owner", "") or "要確認"), "task": str(a.get("task", "")), "due": str(a.get("due", "") or "")}
        for a in (out["actions"] or []) if isinstance(a, dict) and a.get("task")
    ]
    return out
