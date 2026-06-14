"""Gửi tin nhắn / tài liệu ra Telegram qua Bot API (httpx, không cần Application).

Dùng cho job định kỳ và endpoint web để đẩy kết quả ra Telegram.
"""
from __future__ import annotations

import httpx

from .logging_config import get_logger

logger = get_logger(__name__)


class TelegramClient:
    def __init__(self, token: str, timeout: float = 30.0) -> None:
        self.base = f"https://api.telegram.org/bot{token}"
        self.timeout = timeout

    async def send_message(self, chat_id: str, text: str) -> None:
        # Telegram giới hạn 4096 ký tự / tin nhắn -> cắt nếu quá dài.
        for chunk in _split(text, 4000):
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base}/sendMessage",
                    json={"chat_id": chat_id, "text": chunk},
                )
                if resp.status_code != 200:
                    logger.warning("sendMessage lỗi: %s", resp.text)

    async def send_document(self, chat_id: str, path: str, caption: str = "") -> None:
        with open(path, "rb") as fh:
            files = {"document": (path.split("/")[-1], fh)}
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption[:1000]
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base}/sendDocument", data=data, files=files
                )
                if resp.status_code != 200:
                    logger.warning("sendDocument lỗi: %s", resp.text)


def _split(text: str, size: int) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]
