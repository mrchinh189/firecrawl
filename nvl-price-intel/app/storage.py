"""Lưu trữ lịch sử giá và báo cáo.

Mặc định dùng SQLite (luôn chạy được, không cần dịch vụ ngoài). Nếu cấu hình
Supabase (SUPABASE_URL + SUPABASE_KEY) thì dùng Supabase.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import closing

from .config import Settings
from .logging_config import get_logger
from .models import RunResult, TickerSnapshot

logger = get_logger(__name__)


class Storage:
    """Interface lưu trữ."""

    def save_prices(self, snapshot: TickerSnapshot) -> int:  # pragma: no cover
        raise NotImplementedError

    def save_run(self, result: RunResult) -> None:  # pragma: no cover
        raise NotImplementedError


class SQLiteStorage(Storage):
    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with closing(sqlite3.connect(self.path)) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS prices (
                    ticker TEXT NOT NULL,
                    date   TEXT NOT NULL,
                    open   REAL, high REAL, low REAL, close REAL,
                    volume INTEGER,
                    PRIMARY KEY (ticker, date)
                );
                CREATE TABLE IF NOT EXISTS runs (
                    ticker       TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    last_close   REAL,
                    change_pct   REAL,
                    summary      TEXT,
                    docx_path    TEXT,
                    ai_used      INTEGER,
                    PRIMARY KEY (ticker, generated_at)
                );
                """
            )
            conn.commit()

    def save_prices(self, snapshot: TickerSnapshot) -> int:
        with closing(sqlite3.connect(self.path)) as conn:
            rows = [
                (b.ticker, b.date, b.open, b.high, b.low, b.close, b.volume)
                for b in snapshot.bars
            ]
            conn.executemany(
                "INSERT OR REPLACE INTO prices "
                "(ticker, date, open, high, low, close, volume) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
        logger.info("Đã lưu %d phiên %s vào SQLite", len(snapshot.bars), snapshot.ticker)
        return len(snapshot.bars)

    def save_run(self, result: RunResult) -> None:
        ind = result.indicators
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO runs "
                "(ticker, generated_at, last_close, change_pct, summary, docx_path, ai_used) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    result.ticker,
                    result.generated_at,
                    ind.last_close,
                    ind.change_pct,
                    result.summary,
                    result.docx_path,
                    int(result.ai_used),
                ),
            )
            conn.commit()


class SupabaseStorage(Storage):
    def __init__(self, url: str, key: str) -> None:
        from supabase import create_client  # import trễ để không bắt buộc cài

        self.client = create_client(url, key)

    def save_prices(self, snapshot: TickerSnapshot) -> int:
        rows = [b.to_dict() for b in snapshot.bars]
        # upsert theo khoá (ticker, date) — cần unique constraint trong schema.sql
        self.client.table("prices").upsert(rows, on_conflict="ticker,date").execute()
        logger.info("Đã upsert %d phiên %s vào Supabase", len(rows), snapshot.ticker)
        return len(rows)

    def save_run(self, result: RunResult) -> None:
        ind = result.indicators
        self.client.table("runs").insert(
            {
                "ticker": result.ticker,
                "generated_at": result.generated_at,
                "last_close": ind.last_close,
                "change_pct": ind.change_pct,
                "summary": result.summary,
                "docx_path": result.docx_path,
                "ai_used": result.ai_used,
            }
        ).execute()


def get_storage(settings: Settings) -> Storage:
    backend = (settings.storage_backend or "sqlite").lower()
    if backend == "supabase":
        if not (settings.supabase_url and settings.supabase_key):
            logger.warning("Thiếu cấu hình Supabase, fallback sang SQLite")
            return SQLiteStorage(settings.sqlite_path)
        return SupabaseStorage(settings.supabase_url, settings.supabase_key)
    return SQLiteStorage(settings.sqlite_path)
