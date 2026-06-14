# Hướng dẫn triển khai (Deploy)

## 1. Chuẩn bị

| Mục | Cách lấy |
|---|---|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com → API Keys |
| `TELEGRAM_BOT_TOKEN` | Nhắn [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_CHAT_ID` | Nhắn [@userinfobot](https://t.me/userinfobot) (hoặc id nhóm) |
| `API_TOKEN` | Tự đặt 1 chuỗi bí mật để bảo vệ `POST /run` |

Sao chép cấu hình mẫu và điền:
```bash
cp .env.example .env
```

## 2. Deploy bằng Docker Compose (1 server/VPS)

Yêu cầu: Docker + Docker Compose trên VPS Linux. **Mạng phải cho phép egress** tới `apipubaws.tcbs.com.vn` (dữ liệu giá) và `api.anthropic.com` (Claude).

```bash
git clone <repo> && cd nvl-price-intel
cp .env.example .env && nano .env     # điền key
docker compose up -d --build
docker compose logs -f web            # xem log
```

- Service `web`: API + dashboard (cổng 8000) + lịch tự động.
- Service `bot`: bot Telegram.
- Dữ liệu (SQLite + báo cáo) lưu ở `./data` (đã mount volume, không mất khi rebuild).

Mở dashboard: `http://<IP_SERVER>:8000`. Khuyến nghị đặt sau Nginx/Caddy + HTTPS.

### Đưa ra web (HTTPS) với Caddy (ví dụ)
```
your-domain.com {
    reverse_proxy localhost:8000
}
```

## 3. Lịch tự động

Cấu hình trong `.env`:
```
SCHEDULE_ENABLED=true
SCHEDULE_CRON=0 16 * * 1-5     # 16:00 các ngày T2–T6 (giờ VN)
TIMEZONE=Asia/Ho_Chi_Minh
```
Cron 5 trường: `phút giờ ngày tháng thứ`. Job sẽ chạy pipeline cho toàn bộ `TICKERS` rồi gửi Telegram.

## 4. Kích hoạt thủ công

- **Qua web:** `POST /run` (tham số `ticker`, `push=true` để gửi Telegram), header `X-API-Token`.
  ```bash
  curl -X POST "https://your-domain.com/run?push=true" -H "X-API-Token: <API_TOKEN>"
  ```
- **Qua Telegram:** gửi `/capnhat NVL` cho bot.

## 5. Supabase (tuỳ chọn)

1. Tạo project tại https://supabase.com
2. Chạy `supabase/schema.sql` trong SQL Editor.
3. Đặt trong `.env`:
   ```
   STORAGE_BACKEND=supabase
   SUPABASE_URL=https://xxxx.supabase.co
   SUPABASE_KEY=<service_role hoặc anon key có quyền ghi>
   ```

## 6. Vercel (tuỳ chọn — chỉ dashboard tĩnh)

Backend này là dịch vụ chạy nền (lịch + bot + API) nên **không phù hợp chạy serverless trên Vercel**. Nếu muốn dùng Vercel, hãy:
- Triển khai backend (web + bot) bằng Docker trên VPS như mục 2.
- Dùng Vercel cho một frontend riêng (Next.js) gọi tới API `POST /run` và `GET /reports/...` của backend qua domain HTTPS.

## 7. Kiểm tra sức khoẻ

```bash
curl https://your-domain.com/health
```
Trả về trạng thái, danh sách mã, lịch, cờ AI/Telegram.
