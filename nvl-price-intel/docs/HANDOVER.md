# Tài liệu bàn giao — NVL Price Intel

Phiên bản: 1.0.0

## 1. Mục tiêu hệ thống

Tự động hoá quy trình: **cập nhật giá cổ phiếu NVL → phân tích bằng Claude → tạo báo cáo → gửi Telegram**, chạy theo lịch hàng ngày và cho phép kích hoạt thủ công.

## 2. Thành phần & vai trò

| File | Vai trò |
|---|---|
| `app/config.py` | Cấu hình tập trung (đọc `.env`) |
| `app/data_source.py` | Lấy dữ liệu giá (TCBS / mock), interface để mở rộng |
| `app/indicators.py` | Tính SMA, RSI, cao/thấp kỳ, khối lượng TB |
| `app/storage.py` | Lưu giá + lịch sử chạy (SQLite / Supabase) |
| `app/analyzer.py` | Gọi Claude viết phân tích; fallback theo luật khi không có key |
| `app/report.py` | Sinh báo cáo `.docx` |
| `app/telegram_client.py` | Gửi text/document ra Telegram (dùng cho lịch + web) |
| `app/telegram_bot.py` | Bot nhận lệnh `/capnhat`, `/gia` |
| `app/pipeline.py` | Điều phối toàn bộ luồng |
| `app/scheduler.py` | Lịch chạy định kỳ (APScheduler) |
| `app/web.py` | API + dashboard + endpoint kích hoạt thủ công |

## 3. Luồng xử lý (pipeline)

```
fetch (giá) → save_prices → compute_indicators → analyze (Claude) → build_report (.docx) → save_run → [notify Telegram]
```

3 nguồn kích hoạt cùng gọi `pipeline.run_one` / `run_all`:
1. **Lịch** (`scheduler.py`) — hàng ngày theo cron.
2. **Web** (`POST /run`).
3. **Telegram** (`/capnhat`).

## 4. Cấu hình quan trọng (.env)

Xem `.env.example`. Các biến cần điền để dùng đầy đủ:
- `ANTHROPIC_API_KEY` — bật phân tích Claude (không có thì tự fallback).
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — bật bot + gửi định kỳ.
- `API_TOKEN` — bảo vệ `POST /run`.
- `SCHEDULE_CRON`, `TIMEZONE` — lịch tự động.
- `STORAGE_BACKEND` + `SUPABASE_*` — đổi sang Supabase nếu cần.

## 5. Cách vận hành

| Việc | Lệnh |
|---|---|
| Chạy toàn hệ thống | `docker compose up -d --build` |
| Xem log | `docker compose logs -f web` / `... bot` |
| Cập nhật thủ công | `curl -X POST ".../run?ticker=NVL&push=true" -H "X-API-Token: ..."` |
| Cập nhật qua Telegram | gửi `/capnhat NVL` |
| Xem báo cáo | dashboard `/` hoặc `/reports/<file>.docx` |
| Kiểm tra sức khoẻ | `GET /health` |

## 6. Kiểm thử

```bash
pip install -r requirements.txt
pytest          # 14 test, dùng nguồn mock, không cần mạng/Claude
```
Các test phủ: parse dữ liệu, chỉ báo, sinh DOCX, pipeline end-to-end, fallback analyzer.

> Lưu ý: test dùng `DATA_SOURCE=mock` để chạy offline. Khi chạy thật, server cần egress tới TCBS và Anthropic.

## 7. Mở rộng thường gặp

- **Thêm mã:** đặt `TICKERS=NVL,VIC,VHM`.
- **Đổi model Claude:** `ANTHROPIC_MODEL=claude-sonnet-4-6` (rẻ hơn) — mặc định `claude-opus-4-8`.
- **Đổi nguồn dữ liệu:** thêm class kế thừa `DataSource` trong `data_source.py` và đăng ký trong `get_data_source()`.
- **Đổi định dạng báo cáo:** sửa `app/report.py`.

## 8. Giới hạn đã biết

- Phụ thuộc API công khai TCBS (có thể đổi cấu trúc/giới hạn tần suất) — đã có interface để thay nguồn.
- Phân tích AI cần API key Anthropic; không có thì dùng fallback theo luật (kém chi tiết hơn).
- Bot Telegram chạy long-polling (đơn giản, không cần domain công khai); có thể chuyển webhook nếu cần.
- **Sản phẩm dành cho mục đích tham khảo, không phải khuyến nghị đầu tư.**

## 9. Vị trí mã nguồn

Dự án nằm trong thư mục `nvl-price-intel/` (tự chứa hoàn toàn). Có thể tách ra repo riêng (vd `price-intel`) bằng cách copy nguyên thư mục này — không phụ thuộc phần còn lại của monorepo.
