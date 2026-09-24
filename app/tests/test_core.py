"""各ステージで直した不具合が再発しないことを確かめるテスト。

ステージとの対応は codex/Codex開発プロンプト集.md を参照。
"""
import re
from datetime import date
from pathlib import Path

import pytest

from sales_assist.config import get_settings
from sales_assist.dates import format_date, resolve_due
from sales_assist.db import Database
from sales_assist.llm import LLMClient, LLMFormatError, MockLLM, extract_json
from sales_assist.masking import mask, unmask
from sales_assist.services import actions_to_csv, draft_email, generate_minutes, is_overdue

TRANSCRIPT = Path(__file__).resolve().parents[2] / "materials" / "03_商談文字起こし_初回訪問.txt"
TERMS = [("みらい商事株式会社", "COMPANY"), ("みらい商事", "COMPANY"), ("佐藤美和", "PERSON"), ("佐藤", "PERSON"),
         ("田中淳", "PERSON"), ("田中", "PERSON")]


# ステージ1：再起動しても商談が消えない ------------------------------------------
def test_meetings_persist_across_connections(tmp_path):
    path = tmp_path / "t.db"
    mid = Database(path).add_meeting("A社", date(2026, 10, 6), "", "メモ")
    assert Database(path).get_meeting(mid)["customer"] == "A社"


# ステージ2：LLM の出力が ```json で囲まれていても読める ------------------------------
@pytest.mark.parametrize("text", [
    '{"a": 1}',
    '```json\n{"a": 1}\n```',
    '以下が結果です。\n```json\n{"a": 1}\n```\nご確認ください。',
])
def test_extract_json_variants(text):
    assert extract_json(text) == {"a": 1}


def test_extract_json_invalid():
    with pytest.raises(LLMFormatError):
        extract_json("申し訳ありません、作成できませんでした。")


class FlakyLLM(LLMClient):
    """1回目は壊れた出力、2回目は正しい出力を返す。"""

    def __init__(self):
        self.calls = 0

    def complete(self, system, user):
        self.calls += 1
        return "壊れた出力" if self.calls == 1 else '{"summary": "ok", "actions": []}'


def test_generate_minutes_retries_on_format_error():
    llm = FlakyLLM()
    meeting = {"id": 1, "customer": "A社", "meeting_date": "2026-10-06", "attendees": "", "memo": "営業：こんにちは"}
    result = generate_minutes(llm, meeting, [])
    assert llm.calls == 2 and result.minutes["summary"] == "ok"


# ステージ3：全角の電話番号・メールアドレスもマスキングできる --------------------------
@pytest.mark.parametrize("phone", ["080-4127-3395", "08041273395", "０８０－４１２７－３３９５", "080ー4127ー3395",
                                   "03(1234)5678"])
def test_mask_phone_variants(phone):
    assert "[電話番号]" in mask(f"携帯は{phone}です").text


def test_mask_email_fullwidth():
    assert "[メールアドレス]" in mask("ｔａｋａｎｏ.k＠minato-seiki.example.jp まで").text


def test_mask_terms_longest_first_and_unmask():
    r = mask("みらい商事株式会社の佐藤美和です。隣に田中淳も同席。佐藤と田中です。", TERMS)
    assert "みらい商事" not in r.text and "佐藤" not in r.text and "美和" not in r.text and "淳" not in r.text
    assert unmask(r.text, r.mapping) == "みらい商事株式会社の佐藤美和です。隣に田中淳も同席。佐藤と田中です。"


def test_dates_are_not_masked_as_phone():
    assert mask("2026-10-06 と 10月16日").text == "2026-10-06 と 10月16日"


class RecordingLLM(MockLLM):
    def complete(self, system, user):
        self.last_user = user
        return super().complete(system, user)


def test_prompt_sent_to_llm_is_masked():
    llm = RecordingLLM()
    meeting = {"id": 1, "customer": "みらい商事株式会社", "meeting_date": "2026-10-06",
               "attendees": "佐藤様、田中様", "memo": TRANSCRIPT.read_text(encoding="utf-8")}
    generate_minutes(llm, meeting, TERMS)
    for secret in ("みらい商事", "佐藤", "田中"):
        assert secret not in llm.last_user


# ステージ4：メールにマスキングの記号が残らない ----------------------------------------
def test_email_has_no_placeholders():
    meeting = {"id": 1, "customer": "みらい商事株式会社", "meeting_date": "2026-10-06",
               "attendees": "", "memo": TRANSCRIPT.read_text(encoding="utf-8")}
    minutes = generate_minutes(MockLLM(), meeting, TERMS).minutes
    mail = draft_email(MockLLM(), minutes, TERMS, "顧客", "丁寧", "ELI 営業")
    assert "[PERSON_" not in mail["body"] and "[COMPANY_" not in mail["body"]


# ステージ5：相対的な期限を具体的な日付にする ----------------------------------------
BASE = date(2026, 10, 6)  # 火曜日


@pytest.mark.parametrize("expr, expected", [
    ("来週金曜", date(2026, 10, 16)),
    ("来週火曜までに", date(2026, 10, 13)),
    ("来週の金曜日", date(2026, 10, 16)),
    ("今週金曜", date(2026, 10, 9)),
    ("再来週月曜", date(2026, 10, 19)),
    ("10月20日", date(2026, 10, 20)),
    ("１０月２０日", date(2026, 10, 20)),
    ("1月15日", date(2027, 1, 15)),
    ("2026/11/17", date(2026, 11, 17)),
    ("明日", date(2026, 10, 7)),
    ("次回", None),
    ("", None),
    ("2月30日", None),
])
def test_resolve_due(expr, expected):
    assert resolve_due(expr, BASE) == expected


def test_minutes_actions_have_resolved_dates_and_names():
    meeting = {"id": 1, "customer": "みらい商事株式会社", "meeting_date": "2026-10-06",
               "attendees": "", "memo": TRANSCRIPT.read_text(encoding="utf-8")}
    result = generate_minutes(MockLLM(), meeting, TERMS)
    dues = {a["due_date"] for a in result.actions}
    assert {"2026-10-09", "2026-10-12", "2026-10-13"} <= dues
    assert any(a["owner"] == "話者B" and a["due_date"] == "2026-10-13" for a in result.actions)
    assert "[PERSON_" not in str(result.minutes) and "[COMPANY_" not in str(result.minutes)  # 記号が残っていない


def test_actions_sorted_with_undated_last(tmp_path):
    db = Database(tmp_path / "t.db")
    mid = db.add_meeting("A社", BASE, "", "メモ")
    db.save_minutes(mid, {}, [
        {"owner": "x", "task": "未定", "due_text": "次回", "due_date": None},
        {"owner": "x", "task": "遅い", "due_text": "", "due_date": "2026-10-20"},
        {"owner": "x", "task": "早い", "due_text": "", "due_date": "2026-10-13"},
    ])
    assert [a["task"] for a in db.list_actions()] == ["早い", "遅い", "未定"]


def test_regenerating_minutes_does_not_duplicate_actions(tmp_path):
    db = Database(tmp_path / "t.db")
    mid = db.add_meeting("A社", BASE, "", "メモ")
    acts = [{"owner": "x", "task": "t", "due_text": "", "due_date": None}]
    db.save_minutes(mid, {}, acts)
    db.save_minutes(mid, {}, acts)
    assert len(db.list_actions()) == 1


def test_overdue():
    a = {"due_date": "2026-10-13", "status": "未着手"}
    assert is_overdue(a, date(2026, 10, 14))
    assert not is_overdue({**a, "status": "完了"}, date(2026, 10, 14))
    assert not is_overdue({"due_date": None, "status": "未着手"}, date(2026, 10, 14))
    assert format_date(date(2026, 10, 16)) == "2026/10/16（金）"


# ステージ6：CSV を Excel で開いても文字化けしない ------------------------------------
def test_csv_has_bom_for_excel():
    data = actions_to_csv([{"customer": "みらい商事", "meeting_date": "2026-10-06", "owner": "佐藤",
                            "task": "リスト送付", "due_date": "2026-10-13", "due_text": "来週火曜", "status": "未着手"}])
    assert data.startswith(b"\xef\xbb\xbf")
    assert "リスト送付" in data.decode("utf-8-sig")


# ステージ7：API キーがなくても落ちない ----------------------------------------------
def test_missing_api_key_falls_back_to_mock(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    s = get_settings()
    assert s.provider == "mock" and "OPENAI_API_KEY" in s.warning


def test_no_api_key_in_source():
    key_pattern = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
    for py in Path(__file__).resolve().parents[1].rglob("*.py"):
        assert not key_pattern.search(py.read_text(encoding="utf-8")), py
