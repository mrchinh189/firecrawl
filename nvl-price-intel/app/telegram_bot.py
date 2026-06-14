"""Bot Telegram nhận lệnh và trả kết quả cập nhật giá + báo cáo DOCX.

Lệnh hỗ trợ:
  /start, /help   - hướng dẫn
  /capnhat [MÃ]   - chạy cập nhật + phân tích, trả text và file .docx
  /gia [MÃ]       - xem nhanh giá mới nhất (không sinh báo cáo đầy đủ)
"""
from __future__ import annotations

import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .config import get_settings
from .data_source import get_data_source
from .indicators import compute_indicators
from .logging_config import get_logger, setup_logging
from .pipeline import run_one

logger = get_logger(__name__)

HELP = (
    "🤖 *NVL Price Intel Bot*\n\n"
    "/capnhat [MÃ] — cập nhật giá + phân tích (Claude) + gửi báo cáo .docx\n"
    "/gia [MÃ] — xem nhanh giá mới nhất\n"
    "/help — trợ giúp\n\n"
    "Ví dụ: `/capnhat NVL`"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP, parse_mode="Markdown")


async def cmd_gia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = get_settings()
    ticker = (context.args[0].upper() if context.args else settings.ticker_list[0])
    await update.message.reply_text(f"⏳ Đang lấy giá {ticker}...")
    try:
        source = get_data_source(settings.data_source, settings.http_timeout)
        snapshot = await asyncio.to_thread(source.fetch, ticker, settings.history_days)
        ind = compute_indicators(snapshot)
        await update.message.reply_text(
            f"📊 {ticker}\nGiá: {ind.last_close:,.2f} ({ind.change_pct:+.2f}%)\n"
            f"RSI(14): {ind.rsi14} | SMA20: {ind.sma20}\n"
            f"Cao/Thấp kỳ: {ind.high_period} / {ind.low_period}"
        )
    except Exception as exc:  # noqa: BLE001
        await update.message.reply_text(f"❌ Lỗi: {exc}")


async def cmd_capnhat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = get_settings()
    ticker = (context.args[0].upper() if context.args else settings.ticker_list[0])
    await update.message.reply_text(f"⏳ Đang cập nhật & phân tích {ticker}...")
    try:
        result = await asyncio.to_thread(run_one, ticker, settings)
        await update.message.reply_text(f"{result.summary}\n\n{result.analysis}")
        if result.docx_path:
            with open(result.docx_path, "rb") as fh:
                await update.message.reply_document(
                    document=fh, filename=result.docx_path.split("/")[-1],
                    caption=f"Báo cáo {ticker}",
                )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lỗi /capnhat")
        await update.message.reply_text(f"❌ Lỗi: {exc}")


def build_application() -> Application:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("Thiếu TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(CommandHandler(["capnhat", "update"], cmd_capnhat))
    app.add_handler(CommandHandler(["gia", "price"], cmd_gia))
    return app


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("Khởi động Telegram bot (long polling)...")
    app = build_application()
    app.run_polling()


if __name__ == "__main__":
    main()
