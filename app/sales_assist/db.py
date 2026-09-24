"""SQLite によるデータ保存。アプリを再起動しても商談・議事録・アクションが残る。"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

STATUSES = ["未着手", "対応中", "待ち", "完了"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer TEXT NOT NULL,
    meeting_date TEXT NOT NULL,
    attendees TEXT NOT NULL DEFAULT '',
    memo TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS minutes (
    meeting_id INTEGER PRIMARY KEY REFERENCES meetings(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    owner TEXT NOT NULL DEFAULT '',
    task TEXT NOT NULL,
    due_text TEXT NOT NULL DEFAULT '',
    due_date TEXT,
    status TEXT NOT NULL DEFAULT '未着手'
);
CREATE TABLE IF NOT EXISTS mask_terms (
    term TEXT PRIMARY KEY,
    kind TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # --- 商談 ---------------------------------------------------------------
    def add_meeting(self, customer: str, meeting_date: date, attendees: str, memo: str) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO meetings (customer, meeting_date, attendees, memo, created_at) VALUES (?, ?, ?, ?, ?)",
                (customer.strip(), meeting_date.isoformat(), attendees.strip(), memo, _now()),
            )
            return cur.lastrowid

    def list_meetings(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM meetings ORDER BY meeting_date DESC, id DESC").fetchall()
        return [dict(r) for r in rows]

    def get_meeting(self, meeting_id: int) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        return dict(row) if row else None

    def delete_meeting(self, meeting_id: int) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))

    # --- 議事録・アクション ---------------------------------------------------
    def save_minutes(self, meeting_id: int, minutes: dict, actions: list[dict]) -> None:
        """議事録を保存し、その商談のアクションを置き換える（再生成しても重複しない）。"""
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO minutes (meeting_id, content, created_at) VALUES (?, ?, ?)",
                (meeting_id, json.dumps(minutes, ensure_ascii=False), _now()),
            )
            c.execute("DELETE FROM actions WHERE meeting_id = ?", (meeting_id,))
            c.executemany(
                "INSERT INTO actions (meeting_id, owner, task, due_text, due_date, status) VALUES (?, ?, ?, ?, ?, '未着手')",
                [(meeting_id, a["owner"], a["task"], a["due_text"], a["due_date"]) for a in actions],
            )

    def get_minutes(self, meeting_id: int) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT content FROM minutes WHERE meeting_id = ?", (meeting_id,)).fetchone()
        return json.loads(row["content"]) if row else None

    def list_actions(self, include_done: bool = True) -> list[dict]:
        sql = """SELECT a.*, m.customer, m.meeting_date FROM actions a JOIN meetings m ON a.meeting_id = m.id"""
        if not include_done:
            sql += " WHERE a.status != '完了'"
        # 期限が未定（NULL）のものは最後に並べる
        sql += " ORDER BY a.due_date IS NULL, a.due_date, a.id"
        with self._conn() as c:
            return [dict(r) for r in c.execute(sql).fetchall()]

    def update_action(self, action_id: int, status: str | None = None, due_date: date | None = None) -> None:
        with self._conn() as c:
            if status is not None:
                if status not in STATUSES:
                    raise ValueError(f"不正な状態です：{status}")
                c.execute("UPDATE actions SET status = ? WHERE id = ?", (status, action_id))
            if due_date is not None:
                c.execute("UPDATE actions SET due_date = ? WHERE id = ?", (due_date.isoformat(), action_id))

    # --- マスキング用の語句 ---------------------------------------------------
    def list_terms(self) -> list[tuple[str, str]]:
        with self._conn() as c:
            return [(r["term"], r["kind"]) for r in c.execute("SELECT term, kind FROM mask_terms ORDER BY kind, term")]

    def add_term(self, term: str, kind: str) -> None:
        term = term.strip()
        if term:
            with self._conn() as c:
                c.execute("INSERT OR REPLACE INTO mask_terms (term, kind) VALUES (?, ?)", (term, kind))

    def delete_term(self, term: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM mask_terms WHERE term = ?", (term,))


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
