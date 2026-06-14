from alerts import telegram


def test_build_summary_content():
    text = telegram.build_summary()   # offline -> dùng build_analysis fixtures
    assert "PP" in text
    assert "<a href=" in text          # link nguồn/tin
    assert "2026-06-" in text          # ngày giá
    assert ("▲" in text or "▼" in text)
    assert "Tin" in text or "📰" in text


def test_send_text_dry_run(capsys, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    res = telegram.send_text("xin chào")   # thiếu token -> dry-run, không gọi mạng
    assert res is None
    out = capsys.readouterr().out
    assert "dry" in out.lower()
