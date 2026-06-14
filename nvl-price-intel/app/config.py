"""Cấu hình ứng dụng đọc từ biến môi trường / file .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Danh mục theo dõi ---
    # Mặc định NVL (Novaland). Có thể thêm mã khác, phân tách bằng dấu phẩy.
    tickers: str = Field(default="NVL", description="Danh sách mã, vd: NVL,VIC,VHM")
    history_days: int = Field(default=120, description="Số phiên lấy về để tính chỉ báo")

    # --- Nguồn dữ liệu ---
    data_source: str = Field(default="tcbs", description="tcbs | mock")
    http_timeout: float = Field(default=20.0)

    # --- Claude API (Anthropic) ---
    anthropic_api_key: str | None = Field(default=None)
    anthropic_model: str = Field(default="claude-opus-4-8")
    anthropic_max_tokens: int = Field(default=4000)
    # Nếu không có API key -> dùng phân tích fallback theo luật (không cần Claude).
    enable_ai_analysis: bool = Field(default=True)

    # --- Telegram ---
    telegram_bot_token: str | None = Field(default=None)
    telegram_chat_id: str | None = Field(default=None, description="Chat nhận báo cáo định kỳ")

    # --- Lưu trữ ---
    # storage_backend: sqlite | supabase
    storage_backend: str = Field(default="sqlite")
    sqlite_path: str = Field(default="data/price_intel.db")
    supabase_url: str | None = Field(default=None)
    supabase_key: str | None = Field(default=None)

    # --- Lịch chạy (cron, theo timezone bên dưới) ---
    schedule_enabled: bool = Field(default=True)
    schedule_cron: str = Field(default="0 16 * * 1-5", description="Cron: mặc định 16:00 T2-T6")
    timezone: str = Field(default="Asia/Ho_Chi_Minh")

    # --- Web / API ---
    web_host: str = Field(default="0.0.0.0")
    web_port: int = Field(default=8000)
    # Token bảo vệ endpoint /run (gửi qua header X-API-Token)
    api_token: str | None = Field(default=None)
    reports_dir: str = Field(default="data/reports")

    # --- Logging ---
    log_level: str = Field(default="INFO")

    @property
    def ticker_list(self) -> list[str]:
        return [t.strip().upper() for t in self.tickers.split(",") if t.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
