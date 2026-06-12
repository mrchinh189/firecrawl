"""Gui canh bao bien dong gia qua Telegram."""
import logging

import requests

import config

log = logging.getLogger("alert")


def send_telegram(message: str) -> None:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        log.info("Chua cau hinh Telegram, bo qua canh bao: %s", message)
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        log.warning("Gui Telegram that bai: %s", exc)


def check_and_alert(source_name: str, row: dict, previous) -> None:
    """So gia moi voi gia truoc; canh bao neu vuot nguong %."""
    if previous is None or previous[0] in (None, 0):
        return
    old = float(previous[0])
    new = float(row["price_usd_ton"])
    pct = (new - old) / old * 100.0
    if abs(pct) < config.ALERT_THRESHOLD_PCT:
        return

    arrow = "🔺" if pct > 0 else "🔻"
    vnd = row["price_vnd_ton"]
    label = f"{row['material']} {row['grade']} {row['region']}".strip()
    msg = (
        f"{arrow} <b>Bien dong gia {label}</b>\n"
        f"Nguon: {source_name}\n"
        f"Gia: {old:,.0f} → {new:,.0f} USD/tan ({pct:+.1f}%)\n"
        f"≈ {vnd:,.0f} VND/tan\n"
        f"Nguong canh bao: {config.ALERT_THRESHOLD_PCT}%"
    )
    log.info("ALERT: %s %+.1f%%", label, pct)
    send_telegram(msg)
