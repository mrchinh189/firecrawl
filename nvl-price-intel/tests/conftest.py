import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import Settings  # noqa: E402


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Settings cô lập cho test: nguồn mock, không Claude, lưu SQLite tạm."""
    return Settings(
        tickers="NVL",
        history_days=60,
        data_source="mock",
        enable_ai_analysis=False,
        anthropic_api_key=None,
        storage_backend="sqlite",
        sqlite_path=str(tmp_path / "test.db"),
        reports_dir=str(tmp_path / "reports"),
        schedule_enabled=False,
        telegram_bot_token=None,
        telegram_chat_id=None,
    )
