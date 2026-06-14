"""Pipeline lõi: lấy giá -> lưu -> tính chỉ báo -> phân tích -> báo cáo -> (thông báo)."""
from __future__ import annotations

from .analyzer import Analyzer
from .config import Settings, get_settings
from .data_source import get_data_source
from .indicators import compute_indicators
from .logging_config import get_logger
from .models import RunResult
from .report import build_report
from .storage import get_storage
from .telegram_client import TelegramClient

logger = get_logger(__name__)


def run_one(ticker: str, settings: Settings | None = None) -> RunResult:
    """Chạy pipeline cho MỘT mã (đồng bộ, không gửi Telegram)."""
    settings = settings or get_settings()
    source = get_data_source(settings.data_source, settings.http_timeout)
    storage = get_storage(settings)
    analyzer = Analyzer(settings)

    snapshot = source.fetch(ticker, settings.history_days)
    storage.save_prices(snapshot)

    indicators = compute_indicators(snapshot)
    analysis, ai_used = analyzer.analyze(indicators, snapshot)

    summary = _build_summary(ticker, indicators)
    result = RunResult(
        ticker=ticker,
        snapshot=snapshot,
        indicators=indicators,
        analysis=analysis,
        summary=summary,
        ai_used=ai_used,
    )
    result.docx_path = build_report(result, settings.reports_dir)
    storage.save_run(result)
    logger.info("Hoàn tất pipeline %s: %s", ticker, summary.replace("\n", " "))
    return result


def run_all(settings: Settings | None = None) -> list[RunResult]:
    """Chạy pipeline cho toàn bộ danh mục cấu hình."""
    settings = settings or get_settings()
    results: list[RunResult] = []
    for ticker in settings.ticker_list:
        try:
            results.append(run_one(ticker, settings))
        except Exception as exc:  # noqa: BLE001 - không để 1 mã lỗi chặn cả lô
            logger.error("Lỗi pipeline %s: %s", ticker, exc)
    return results


async def notify(result: RunResult, settings: Settings | None = None) -> None:
    """Gửi tóm tắt + file DOCX ra Telegram (nếu đã cấu hình)."""
    settings = settings or get_settings()
    if not (settings.telegram_bot_token and settings.telegram_chat_id):
        logger.info("Bỏ qua Telegram (chưa cấu hình token/chat_id)")
        return
    client = TelegramClient(settings.telegram_bot_token)
    chat_id = settings.telegram_chat_id
    text = f"{result.summary}\n\n{result.analysis}"
    await client.send_message(chat_id, text)
    if result.docx_path:
        await client.send_document(
            chat_id, result.docx_path, caption=f"Báo cáo {result.ticker}"
        )


async def run_all_and_notify(settings: Settings | None = None) -> list[RunResult]:
    """Chạy toàn danh mục rồi gửi Telegram — dùng cho lịch định kỳ."""
    settings = settings or get_settings()
    results = run_all(settings)
    for result in results:
        await notify(result, settings)
    return results


def _build_summary(ticker: str, indicators) -> str:
    arrow = "🔺" if indicators.change_pct > 0 else ("🔻" if indicators.change_pct < 0 else "➖")
    return (
        f"📊 {ticker} | Giá: {indicators.last_close:,.2f} "
        f"{arrow} {indicators.change_pct:+.2f}% "
        f"| RSI: {indicators.rsi14} | SMA20: {indicators.sma20}"
    )
