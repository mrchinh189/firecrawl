# -*- coding: utf-8 -*-
"""llm.py — wrapper Claude API fail-soft + prompt caching. Thiếu ANTHROPIC_API_KEY -> None."""
import os
import functools
import pathlib
import yaml

CFG = pathlib.Path(__file__).resolve().parent / "config" / "models.yaml"


@functools.lru_cache(maxsize=1)
def _cfg():
    if CFG.exists():
        return yaml.safe_load(CFG.read_text(encoding="utf-8")) or {}
    return {}


def model_for(task: str) -> str:
    c = _cfg()
    return c.get(task) or c.get("narrative") or "claude-opus-4-8"


def complete(task: str, system: str, user: str, max_tokens=None):
    """Gọi Claude 1 lượt. system được cache (prompt caching). Trả text hoặc None nếu thiếu key/lỗi."""
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return None
    try:
        import anthropic

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model_for(task),
            max_tokens=max_tokens or _cfg().get("max_tokens", 2000),
            system=[{"type": "text", "text": system,
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    except Exception as e:  # noqa: BLE001 - fail-soft
        print(f"[WARN] llm.complete({task}) lỗi: {e}")
        return None
