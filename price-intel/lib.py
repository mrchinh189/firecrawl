# -*- coding: utf-8 -*-
"""lib.py — helper thuần dùng chung (không phụ thuộc DB/mạng): nạp YAML, độ tươi, link nguồn."""
import datetime as dt
import functools
import pathlib
import yaml

CONFIG = pathlib.Path(__file__).resolve().parent / "config"


@functools.lru_cache(maxsize=None)
def load_yaml(name: str):
    """Nạp config/<name>.yaml. Trả {} nếu không có file."""
    p = CONFIG / name
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def freshness(date_val, today=None) -> dict:
    """Độ tươi từ ngày của giá: 🟢 ≤7 · 🟡 ≤30 · 🔴 >30 ngày."""
    today = today or dt.date.today()
    d = date_val if isinstance(date_val, dt.date) else dt.date.fromisoformat(str(date_val)[:10])
    days = (today - d).days
    emoji = "🟢" if days <= 7 else "🟡" if days <= 30 else "🔴"
    return {"emoji": emoji, "days": days, "date": d.isoformat()}


def source_link(name: str):
    """Tra (label, url|None) từ source_links.yaml. Nguồn lạ -> (name, None)."""
    table = load_yaml("source_links.yaml")
    entry = table.get(name)
    if not entry:
        return (name, None)
    return (entry.get("label", name), entry.get("url"))
