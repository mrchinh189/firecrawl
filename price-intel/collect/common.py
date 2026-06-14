# -*- coding: utf-8 -*-
"""common.py — tiện ích chung cho collectors: đọc env (fail-soft), kết nối DB, delay lịch sự."""
import os
import time


def env(key, default=None):
    v = os.getenv(key, "")
    return v.strip() if v else default


def has(*keys) -> bool:
    """True nếu CÓ ĐỦ tất cả khóa env (để SKIP nguồn khi thiếu khóa)."""
    return all(env(k) for k in keys)


def polite_sleep(seconds=4):
    """Delay lịch sự giữa các request (tôn trọng ToS/robots)."""
    try:
        time.sleep(float(seconds))
    except Exception:
        pass


def db():
    """Kết nối Postgres (Supabase) nếu có SUPABASE_DB_URL; không thì raise để caller fallback fixtures."""
    url = env("SUPABASE_DB_URL")
    if not url:
        raise RuntimeError("Thiếu SUPABASE_DB_URL — dùng fixtures")
    import psycopg2
    return psycopg2.connect(url)
