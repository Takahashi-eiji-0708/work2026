"""LLM の呼び出し。mock（教材用・API キー不要）と openai を切り替えられる。"""
import json
import re

from .config import Settings
from .prompts import EMAIL_SYSTEM, MINUTES_SYSTEM


class LLMFormatError(Exception):
    """LLM の出力が期待した JSON 形式でなかった。"""


def extract_json(text: str) -> dict:
    """LLM の出力から JSON オブジェクトを取り出す。

    実際の LLM は ```json で囲んだり、前置きの一文を付けたりすることがあるため、
    最初の { から最後の } までを取り出して解析する。
    """
    if not text:
        raise LLMFormatError("LLM の出力が空でした。")
    cleaned = re.sub(r"```(?:json)?", "", text)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise LLMFormatError("LLM の出力に JSON が見つかりませんでした。")
    try:
        data = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError as e:
        raise LLMFormatError(f"LLM の出力を JSON として読めませんでした（{e.msg}）。") from e
    if not isinstance(data, dict):
        raise LLMFormatError("LLM の出力が JSON オブジェクトではありませんでした。")
    return data


class LLMClient:
    name = "base"

    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class OpenAIClient(LLMClient):
    name = "openai"

    def __init__(self, api_key: str, model: str):
        from openai import OpenAI  # モックモードでは openai パッケージがなくても動くように遅延 import

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or ""


class MockLLM(LLMClient):
    """API キーなしで動く教材用のモック。

    商談メモからキーワードで簡易的に議事録を組み立てる。実際の LLM の癖を再現するため、
    応答は前置きの一文と ```json のコードブロックで返す。
    """

    name = "mock"
    ACTION_WORDS = ("お送りします", "確認しておきます", "お伝えします", "送付します", "ご連絡します", "作成します")
    CONCERN_WORDS = ("悩み", "懸念", "怖い", "不評", "許可", "コスト", "しにくかった", "使えない")
    BACKGROUND_WORDS = ("中期経営計画", "DX", "定年", "技能伝承", "たまってる", "分析")
    REQUIREMENT_RULES = (
        ("対象", ("年目", "名くらい")),
        ("期間", ("日くらい",)),
        ("時期", ("月から", "年度内")),
        ("予算", ("予算",)),
        ("効果測定", ("効果測定", "何が変わった")),
    )
    DUE_RE = re.compile(r"(再来週|来週|今週)の?[月火水木金土日]曜?|\d{1,2}月\d{1,2}日|明日|明後日|次回")

    def complete(self, system: str, user: str) -> str:
        data = self._email(user) if system == EMAIL_SYSTEM else self._minutes(user)
        body = json.dumps(data, ensure_ascii=False, indent=2)
        return f"以下が結果です。\n```json\n{body}\n```"

    # --- 議事録 -------------------------------------------------------------
    def _minutes(self, user: str) -> dict:
        memo = re.split(r"商談メモ[:：]", user, maxsplit=1)[-1]
        utterances = []
        for line in memo.splitlines():
            m = re.match(r"^\s*([^:：\s]{1,15})\s*[:：]\s*(.+)$", line)
            if m:
                utterances.append((m[1], m[2]))
        background, concerns, decisions, actions, reqs = [], [], [], [], {}
        for speaker, text in utterances:
            sentences = [s for s in re.split(r"(?<=[。？！?])", text) if s.strip()]
            due = ""
            for s in sentences:
                s = s.strip()
                found = self.DUE_RE.search(s)
                if found:
                    due = found[0]
                if any(w in s for w in self.BACKGROUND_WORDS) and len(background) < 4 and speaker != "営業":
                    background.append(s)
                if any(w in s for w in self.CONCERN_WORDS):
                    concerns.append(s)
                # 質問や自社（営業）側の発言は要件として扱わない
                is_question = s.endswith(("か。", "か？", "?")) or speaker == "営業"
                for item, words in self.REQUIREMENT_RULES:
                    if item not in reqs and not is_question and any(w in s for w in words):
                        reqs[item] = s
                if re.search(r"\d{1,2}月\d{1,2}日", s) and ("どうでしょう" in s or "伺います" in s):
                    decisions.append(f"次回打ち合わせ：{s}")
                if any(w in s for w in self.ACTION_WORDS):
                    owner_m = re.search(r"(\[PERSON_\d+\])のほうで", s)
                    actions.append({"owner": owner_m[1] if owner_m else speaker, "task": s, "due": due})
        return {
            "summary": "【モック出力】" + " / ".join(background[:2]),
            "background": background,
            "requirements": [{"item": k, "detail": v} for k, v in reqs.items()],
            "concerns": concerns[:5],
            "decisions": decisions[:3],
            "actions": actions,
        }

    # --- メール -------------------------------------------------------------
    def _email(self, user: str) -> dict:
        recipient = re.search(r"宛先[:：](.+)", user)[1].strip()
        sender = re.search(r"差出人[:：](.+)", user)[1].strip()
        minutes = extract_json(re.split(r"議事録[:：]", user, maxsplit=1)[-1])
        acts = "\n".join(f"・{a.get('owner', '')}：{a.get('task', '')}（{a.get('due_label', a.get('due', ''))}）"
                         for a in minutes.get("actions", []))
        reqs = "\n".join(f"・{r.get('item')}：{r.get('detail')}" for r in minutes.get("requirements", []))
        if recipient == "社内":
            body = (f"【結論】{minutes.get('summary', '')}\n\n【ポイント】\n{reqs}\n\n"
                    f"【相談】（ここに上長への相談事項を書く）\n\n【次の一手】\n{acts}\n\n{sender}")
            return {"subject": "【商談報告】（モック）", "body": body}
        body = ("いつも大変お世話になっております。\n本日はお時間をいただき、誠にありがとうございました。\n\n"
                f"■ 本日伺った内容（当方の理解）\n{reqs}\n\n■ 今後の進め方\n{acts}\n\n"
                "認識に相違がございましたら、ご指摘いただけますと幸いです。\n引き続きよろしくお願いいたします。\n\n"
                f"{sender}")
        return {"subject": "本日のお打ち合わせのお礼（モック）", "body": body}


def create_client(settings: Settings) -> LLMClient:
    if settings.provider == "openai":
        return OpenAIClient(settings.api_key, settings.model)
    return MockLLM()


# 画面から参照するためにエクスポート
__all__ = ["LLMClient", "LLMFormatError", "MockLLM", "OpenAIClient", "create_client", "extract_json",
           "MINUTES_SYSTEM", "EMAIL_SYSTEM"]
