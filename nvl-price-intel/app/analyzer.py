"""Sinh báo cáo phân tích bằng Claude API (Anthropic).

Nếu không cấu hình ANTHROPIC_API_KEY hoặc tắt AI, dùng phân tích fallback
theo luật để hệ thống vẫn chạy được (không phụ thuộc cứng vào Claude).
"""
from __future__ import annotations

from .config import Settings
from .logging_config import get_logger
from .models import Indicators, TickerSnapshot

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Bạn là chuyên gia phân tích cổ phiếu thị trường Việt Nam. "
    "Hãy viết báo cáo phân tích NGẮN GỌN, KHÁCH QUAN bằng tiếng Việt dựa trên "
    "dữ liệu giá và chỉ báo kỹ thuật được cung cấp. Tập trung vào: (1) diễn biến "
    "giá gần đây, (2) tín hiệu kỹ thuật (xu hướng, RSI, đường trung bình, khối "
    "lượng), (3) các mức hỗ trợ/kháng cự đáng chú ý, (4) nhận định rủi ro. "
    "KHÔNG bịa số liệu ngoài dữ liệu đã cho. Luôn kèm câu lưu ý đây không phải "
    "khuyến nghị đầu tư."
)


def _format_facts(ticker: str, ind: Indicators, snapshot: TickerSnapshot) -> str:
    recent = snapshot.bars[-10:]
    lines = [f"- {b.date}: đóng cửa {b.close}, KL {b.volume:,}" for b in recent]
    return (
        f"Mã: {ticker}\n"
        f"Giá đóng cửa gần nhất: {ind.last_close}\n"
        f"Phiên trước: {ind.prev_close}\n"
        f"Thay đổi: {ind.change} ({ind.change_pct}%)\n"
        f"SMA5: {ind.sma5} | SMA20: {ind.sma20}\n"
        f"RSI(14): {ind.rsi14}\n"
        f"Cao nhất kỳ: {ind.high_period} | Thấp nhất kỳ: {ind.low_period}\n"
        f"KL phiên gần nhất: {ind.last_volume:,} | KL TB20: {ind.avg_vol20}\n"
        f"10 phiên gần nhất:\n" + "\n".join(lines)
    )


def _fallback_analysis(ticker: str, ind: Indicators, snapshot: TickerSnapshot) -> str:
    """Phân tích theo luật khi không dùng Claude."""
    trend = "đi ngang"
    if ind.sma5 and ind.sma20:
        if ind.sma5 > ind.sma20:
            trend = "xu hướng tăng ngắn hạn (SMA5 > SMA20)"
        elif ind.sma5 < ind.sma20:
            trend = "xu hướng giảm ngắn hạn (SMA5 < SMA20)"

    rsi_note = "trung tính"
    if ind.rsi14 is not None:
        if ind.rsi14 >= 70:
            rsi_note = f"vùng quá mua (RSI {ind.rsi14})"
        elif ind.rsi14 <= 30:
            rsi_note = f"vùng quá bán (RSI {ind.rsi14})"
        else:
            rsi_note = f"trung tính (RSI {ind.rsi14})"

    direction = "tăng" if ind.change_pct > 0 else ("giảm" if ind.change_pct < 0 else "không đổi")
    return (
        f"Mã {ticker} đóng cửa {ind.last_close}, {direction} {abs(ind.change_pct)}% "
        f"so với phiên trước. Theo các đường trung bình động, cổ phiếu đang ở "
        f"{trend}. Chỉ báo RSI cho thấy {rsi_note}. Vùng giá dao động trong kỳ "
        f"quan sát: thấp nhất {ind.low_period} – cao nhất {ind.high_period}; đây là "
        f"các mốc hỗ trợ/kháng cự tham khảo. Khối lượng phiên gần nhất "
        f"{ind.last_volume:,} so với trung bình 20 phiên {ind.avg_vol20}.\n\n"
        "Lưu ý: Đây là phân tích tự động theo luật kỹ thuật, KHÔNG phải khuyến "
        "nghị đầu tư. (Bật ANTHROPIC_API_KEY để có báo cáo chi tiết từ Claude.)"
    )


class Analyzer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def analyze(self, ind: Indicators, snapshot: TickerSnapshot) -> tuple[str, bool]:
        """Trả về (nội_dung_phân_tích, đã_dùng_AI)."""
        s = self.settings
        if not (s.enable_ai_analysis and s.anthropic_api_key):
            logger.info("Dùng phân tích fallback (không có Claude API key)")
            return _fallback_analysis(snapshot.ticker, ind, snapshot), False

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=s.anthropic_api_key)
            facts = _format_facts(snapshot.ticker, ind, snapshot)
            with client.messages.stream(
                model=s.anthropic_model,
                max_tokens=s.anthropic_max_tokens,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": facts}],
            ) as stream:
                message = stream.get_final_message()

            text = "".join(
                block.text for block in message.content if block.type == "text"
            ).strip()
            if not text:
                raise RuntimeError("Claude trả về rỗng")
            logger.info("Đã sinh phân tích Claude cho %s", snapshot.ticker)
            return text, True
        except Exception as exc:  # noqa: BLE001 - fallback an toàn khi lỗi mạng/API
            logger.warning("Lỗi gọi Claude (%s) -> dùng fallback", exc)
            return _fallback_analysis(snapshot.ticker, ind, snapshot), False
