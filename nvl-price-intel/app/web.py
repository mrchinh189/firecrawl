"""Ứng dụng web FastAPI: dashboard, kích hoạt thủ công, tải báo cáo, lịch tự động."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from .config import get_settings
from .logging_config import get_logger, setup_logging
from .pipeline import notify, run_all, run_one
from .scheduler import build_scheduler

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    scheduler = None
    if settings.schedule_enabled:
        scheduler = build_scheduler(settings)
        scheduler.start()
    app.state.scheduler = scheduler
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(title="NVL Price Intel", version="1.0.0", lifespan=lifespan)


def _check_token(token: str | None) -> None:
    settings = get_settings()
    if settings.api_token and token != settings.api_token:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "tickers": settings.ticker_list,
        "schedule": settings.schedule_cron if settings.schedule_enabled else None,
        "ai_enabled": bool(settings.enable_ai_analysis and settings.anthropic_api_key),
        "telegram": bool(settings.telegram_bot_token and settings.telegram_chat_id),
    }


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    settings = get_settings()
    rows = ""
    reports_dir = settings.reports_dir
    if os.path.isdir(reports_dir):
        for name in sorted(os.listdir(reports_dir), reverse=True)[:20]:
            rows += f'<li><a href="/reports/{name}">{name}</a></li>'
    return f"""
    <html><head><meta charset="utf-8"><title>NVL Price Intel</title></head>
    <body style="font-family: sans-serif; max-width: 720px; margin: 40px auto;">
      <h1>📊 NVL Price Intel</h1>
      <p>Theo dõi: <b>{', '.join(settings.ticker_list)}</b></p>
      <p>Lịch tự động: <code>{settings.schedule_cron}</code> ({settings.timezone})</p>
      <p>Kích hoạt thủ công: <code>POST /run</code> (header <code>X-API-Token</code>)</p>
      <h2>Báo cáo gần đây</h2>
      <ul>{rows or '<li>(chưa có)</li>'}</ul>
    </body></html>
    """


@app.post("/run")
async def trigger_run(
    ticker: str | None = None,
    push: bool = False,
    x_api_token: str | None = Header(default=None),
) -> dict:
    """Kích hoạt cập nhật thủ công. push=True để gửi luôn ra Telegram."""
    _check_token(x_api_token)
    settings = get_settings()
    if ticker:
        results = [run_one(ticker.upper(), settings)]
    else:
        results = run_all(settings)
    if push:
        for r in results:
            await notify(r, settings)
    return {
        "count": len(results),
        "results": [
            {
                "ticker": r.ticker,
                "summary": r.summary,
                "ai_used": r.ai_used,
                "docx": os.path.basename(r.docx_path) if r.docx_path else None,
            }
            for r in results
        ],
    }


@app.get("/reports/{filename}")
def get_report(filename: str) -> FileResponse:
    settings = get_settings()
    safe = os.path.basename(filename)
    path = os.path.join(settings.reports_dir, safe)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo")
    return FileResponse(path, filename=safe)


def main() -> None:
    import uvicorn

    settings = get_settings()
    setup_logging(settings.log_level)
    uvicorn.run("app.web:app", host=settings.web_host, port=settings.web_port)


if __name__ == "__main__":
    main()
