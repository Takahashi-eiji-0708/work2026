"""設定の読み込み。API キーはコードに書かず、環境変数または .env から読む。"""
import os
from dataclasses import dataclass
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path = APP_DIR / ".env") -> None:
    """.env を読み、未設定の環境変数だけを設定する（外部ライブラリなしの簡易版）。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass
class Settings:
    provider: str
    api_key: str
    model: str
    db_path: Path
    warning: str = ""


def get_settings() -> Settings:
    load_dotenv()
    provider = os.environ.get("LLM_PROVIDER", "mock").strip().lower() or "mock"
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_MODEL", "gpt-5-mini").strip()
    db_path = Path(os.environ.get("DB_PATH", "data/sales_assist.db"))
    if not db_path.is_absolute():
        db_path = APP_DIR / db_path
    warning = ""
    if provider not in ("mock", "openai"):
        warning = f"LLM_PROVIDER の値「{provider}」は使えません。モックモードで起動しました。"
        provider = "mock"
    elif provider == "openai" and not api_key:
        warning = "OPENAI_API_KEY が設定されていないため、モックモードで起動しました。.env を確認してください。"
        provider = "mock"
    return Settings(provider, api_key, model, db_path, warning)
