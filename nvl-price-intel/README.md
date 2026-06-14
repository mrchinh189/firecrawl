# 📊 NVL Price Intel

Hệ thống tự động **cập nhật giá cổ phiếu** (mặc định NVL — Novaland), **phân tích bằng Claude API**, và **gửi kết quả qua Telegram** (tin nhắn text + báo cáo `.docx`). Chạy **theo lịch hàng ngày** và **kích hoạt thủ công khi cần**. Deploy bằng `docker-compose`, hỗ trợ Supabase và Vercel (tuỳ chọn).

> ⚠️ Báo cáo mang tính tham khảo, **không phải khuyến nghị đầu tư**.

## Tính năng

| Tính năng | Mô tả |
|---|---|
| Cập nhật giá | Lấy nến ngày từ API công khai TCBS (không cần key), pluggable sang nguồn khác |
| Chỉ báo kỹ thuật | SMA5/20, RSI(14), cao/thấp kỳ, khối lượng TB |
| Phân tích AI | Claude (`claude-opus-4-8`) viết báo cáo tiếng Việt; tự fallback theo luật nếu không có key |
| Báo cáo DOCX | Sinh file Word có bảng giá + chỉ báo + nhận định |
| Telegram | Bot lệnh `/capnhat`, `/gia` + đẩy báo cáo định kỳ |
| Lịch tự động | APScheduler theo cron (mặc định 16:00 T2–T6, giờ VN) |
| Kích hoạt thủ công | `POST /run` (web) hoặc lệnh Telegram |
| Lưu trữ | SQLite mặc định; Supabase tuỳ chọn |

## Kiến trúc

```
                 ┌───────────────┐
   Lịch (cron) ──▶│               │
   /run (web)  ──▶│   pipeline    │──▶ TCBS ──▶ chỉ báo ──▶ Claude ──▶ DOCX
   /capnhat (TG)─▶│               │                                   │
                 └──────┬────────┘                                   ▼
                        │                              SQLite/Supabase + Telegram
        web (FastAPI + APScheduler)  ·  bot (python-telegram-bot)
```

## Chạy nhanh (local)

```bash
cp .env.example .env          # điền ANTHROPIC_API_KEY, TELEGRAM_* nếu có
pip install -r requirements.txt
python -m app.web             # API + dashboard tại http://localhost:8000
python -m app.telegram_bot    # bot Telegram (cửa sổ khác)
```

Kích hoạt thủ công:
```bash
curl -X POST "http://localhost:8000/run?ticker=NVL&push=true" -H "X-API-Token: <API_TOKEN>"
```

## Chạy bằng Docker

```bash
cp .env.example .env
docker compose up -d --build
```

## Test

```bash
pip install -r requirements.txt
pytest
```

Tài liệu chi tiết: [docs/DEPLOY.md](docs/DEPLOY.md) · [docs/HANDOVER.md](docs/HANDOVER.md)
