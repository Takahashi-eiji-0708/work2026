"""ELI Sales Assist — 商談後の議事録・メール下書き・行動管理を支援する研修用サンプルアプリ。

起動：streamlit run app.py
"""
import logging
from datetime import date

import streamlit as st

from sales_assist.config import get_settings
from sales_assist.db import STATUSES, Database
from sales_assist.dates import format_date
from sales_assist.llm import LLMFormatError, create_client
from sales_assist.masking import CATEGORY_LABELS
from sales_assist.services import (actions_to_csv, build_minutes_prompt, draft_email, generate_minutes,
                                   is_overdue, minutes_to_text)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

st.set_page_config(page_title="ELI Sales Assist", page_icon="📋", layout="wide")


@st.cache_resource
def _init():
    settings = get_settings()
    return settings, Database(settings.db_path), create_client(settings)


settings, db, llm = _init()

# --- サイドバー ---------------------------------------------------------------
with st.sidebar:
    st.title("ELI Sales Assist")
    st.caption("商談後の作業を支援する研修用サンプルアプリ")
    st.write(f"**AI の接続先**：{'OpenAI API（' + settings.model + '）' if settings.provider == 'openai' else 'モック（教材用）'}")
    if settings.warning:
        st.warning(settings.warning)
    today = st.date_input("今日の日付（期限切れの判定に使用）", value=date.today())
    st.info("研修では架空のデータだけを入力してください。実際の顧客情報は入力しないでください。")

meetings = db.list_meetings()
meeting_options = {m["id"]: f"{m['meeting_date']}　{m['customer']}（#{m['id']}）" for m in meetings}

tab_reg, tab_min, tab_mail, tab_act, tab_mask = st.tabs(["商談登録", "議事録", "メール下書き", "行動管理", "マスキング設定"])

# --- 商談登録 -----------------------------------------------------------------
with tab_reg:
    st.subheader("商談を登録する")
    with st.form("meeting_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        customer = c1.text_input("顧客名 *")
        meeting_date = c2.date_input("商談日 *", value=date.today())
        attendees = st.text_input("出席者", placeholder="例：佐藤様（人材開発）、田中様（営業企画）、高橋")
        memo = st.text_area("商談メモ・文字起こし *", height=260)
        submitted = st.form_submit_button("登録する", type="primary")
    if submitted:
        if not customer.strip() or not memo.strip():
            st.error("顧客名と商談メモは必須です。")
        else:
            new_id = db.add_meeting(customer, meeting_date, attendees, memo)
            st.session_state["selected_meeting"] = new_id
            st.toast(f"商談 #{new_id} を登録しました。")
            st.rerun()

    st.subheader("登録済みの商談")
    if not meetings:
        st.caption("まだ登録されていません。")
    for m in meetings:
        with st.expander(meeting_options[m["id"]]):
            st.write(f"出席者：{m['attendees'] or '—'}")
            st.text(m["memo"][:500] + ("…" if len(m["memo"]) > 500 else ""))
            if st.button("この商談を削除", key=f"del_{m['id']}"):
                db.delete_meeting(m["id"])
                st.rerun()


def select_meeting(key: str):
    if not meetings:
        st.info("先に「商談登録」タブで商談を登録してください。")
        return None
    ids = list(meeting_options)
    default = st.session_state.get("selected_meeting")
    index = ids.index(default) if default in ids else 0
    return st.selectbox("商談を選ぶ", ids, index=index, format_func=meeting_options.get, key=key)


# --- 議事録 -------------------------------------------------------------------
with tab_min:
    st.subheader("議事録を生成する")
    mid = select_meeting("min_meeting")
    if mid:
        meeting = db.get_meeting(mid)
        terms = db.list_terms()
        prompt, masked = build_minutes_prompt(meeting, terms)
        with st.expander("AI に送る内容を確認する（マスキング済み）", expanded=False):
            st.caption("置き換えた件数：" + ("、".join(f"{k} {v}件" for k, v in masked.counts.items()) or "なし"))
            st.text(prompt)
        confirmed = st.checkbox("AI に送る内容を確認しました（個人情報・未公開情報が残っていない）", key=f"ok_{mid}")
        if st.button("議事録を生成", type="primary", disabled=not confirmed):
            try:
                with st.spinner("生成しています…"):
                    result = generate_minutes(llm, meeting, terms)
                db.save_minutes(mid, result.minutes, result.actions)
                st.success(f"議事録を保存しました。アクション {len(result.actions)} 件を行動管理に登録しました。")
            except LLMFormatError as e:
                st.error(f"AI の出力を読み取れませんでした。もう一度お試しください。（{e}）")
            except Exception:
                logging.getLogger("sales_assist").exception("minutes generation failed meeting_id=%s", mid)
                st.error("議事録の生成中にエラーが発生しました。接続設定（.env）を確認してください。")

        minutes = db.get_minutes(mid)
        if minutes:
            st.markdown("#### 要約")
            st.write(minutes["summary"])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 背景・目的")
                for x in minutes["background"]:
                    st.write(f"・{x}")
                st.markdown("#### 懸念・課題")
                for x in minutes["concerns"]:
                    st.write(f"・{x}")
            with c2:
                st.markdown("#### 確認した要件")
                st.table([{"項目": r.get("item"), "内容": r.get("detail")} for r in minutes["requirements"]])
                st.markdown("#### 決定事項")
                for x in minutes["decisions"]:
                    st.write(f"・{x}")
            st.markdown("#### 次回までのアクション")
            st.table([{"担当": a["owner"], "内容": a["task"], "期限": a.get("due_label", "要確認")} for a in minutes["actions"]])
            st.download_button("議事録をテキストで保存", minutes_to_text(minutes).encode("utf-8-sig"),
                               file_name=f"議事録_{mid}.txt", mime="text/plain")
            st.caption("AI の出力は下書きです。決定事項・期限・担当は必ず自分の記録と照合してください。")

# --- メール下書き ---------------------------------------------------------------
with tab_mail:
    st.subheader("メールを下書きする")
    mid = select_meeting("mail_meeting")
    if mid:
        minutes = db.get_minutes(mid)
        if not minutes:
            st.info("先に「議事録」タブで議事録を生成してください。")
        else:
            c1, c2, c3 = st.columns(3)
            recipient = c1.radio("宛先", ["顧客", "社内"], horizontal=True)
            tone = c2.selectbox("トーン", ["丁寧", "標準", "簡潔"])
            sender = c3.text_input("差出人（署名）", value="ELIソリューションズ 営業部")
            if st.button("下書きを作成", type="primary"):
                try:
                    with st.spinner("作成しています…"):
                        st.session_state[f"mail_{mid}"] = draft_email(llm, minutes, db.list_terms(), recipient, tone, sender)
                except LLMFormatError as e:
                    st.error(f"AI の出力を読み取れませんでした。もう一度お試しください。（{e}）")
                except Exception:
                    logging.getLogger("sales_assist").exception("email draft failed meeting_id=%s", mid)
                    st.error("メールの作成中にエラーが発生しました。接続設定（.env）を確認してください。")
            mail = st.session_state.get(f"mail_{mid}")
            if mail:
                st.text_input("件名", value=mail["subject"])
                st.text_area("本文", value=mail["body"], height=360)
                st.caption("このアプリはメールを送信しません。宛名・敬称・日付・顧客に見せてよい内容かを確認してから、メールソフトに貼り付けてください。")

# --- 行動管理 -------------------------------------------------------------------
with tab_act:
    st.subheader("行動管理")
    show_done = st.checkbox("完了したものも表示", value=False)
    actions = db.list_actions(include_done=show_done)
    if not actions:
        st.caption("アクションはありません。議事録を生成すると、ここに登録されます。")
    else:
        overdue = [a for a in actions if is_overdue(a, today)]
        if overdue:
            st.error(f"期限切れのアクションが {len(overdue)} 件あります。")
        for a in actions:
            c1, c2, c3, c4 = st.columns([2, 5, 2, 2])
            due = date.fromisoformat(a["due_date"]) if a["due_date"] else None
            mark = "🔴 " if is_overdue(a, today) else ""
            c1.write(f"{mark}**{format_date(due)}**")
            c2.write(f"{a['task']}  \n担当：{a['owner']}　／　{a['customer']}（{a['meeting_date']}）")
            new_status = c3.selectbox("状態", STATUSES, index=STATUSES.index(a["status"]), key=f"st_{a['id']}",
                                      label_visibility="collapsed")
            if new_status != a["status"]:
                db.update_action(a["id"], status=new_status)
                st.rerun()
            if not due:
                new_due = c4.date_input("期限を設定", value=None, key=f"due_{a['id']}", label_visibility="collapsed")
                if new_due:
                    db.update_action(a["id"], due_date=new_due)
                    st.rerun()
        st.download_button("CSV で保存（Excel で開けます）", actions_to_csv(db.list_actions()),
                           file_name=f"行動リスト_{today.isoformat()}.csv", mime="text/csv")

# --- マスキング設定 ---------------------------------------------------------------
with tab_mask:
    st.subheader("マスキングする語句")
    st.caption("ここに登録した社名・人名は、AI に送る前に記号に置き換え、結果を表示するときに元に戻します。"
               "電話番号とメールアドレスは登録しなくても自動で置き換えます（元には戻しません）。")
    with st.form("term_form", clear_on_submit=True):
        c1, c2 = st.columns([3, 1])
        term = c1.text_input("語句（例：みらい商事、佐藤美和、佐藤）")
        kind = c2.selectbox("種類", list(CATEGORY_LABELS), format_func=CATEGORY_LABELS.get)
        if st.form_submit_button("追加"):
            db.add_term(term, kind)
            st.rerun()
    for t, k in db.list_terms():
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(t)
        c2.write(CATEGORY_LABELS.get(k, k))
        if c3.button("削除", key=f"term_{t}"):
            db.delete_term(t)
            st.rerun()
