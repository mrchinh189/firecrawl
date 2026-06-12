# Runbook vận hành — Hệ thống theo dõi giá nhựa PP/PE

Tài liệu vận hành cho người quản trị. Mọi lệnh chạy trong thư mục
`examples/plastic-resin-price-tracker`.

## 1. Khởi động / dừng / cập nhật

```bash
docker compose up -d --build      # khởi động (build lần đầu)
docker compose ps                 # trạng thái các service
docker compose down               # dừng (giữ dữ liệu trong volume pgdata)
docker compose down -v            # dừng + XOÁ dữ liệu (cẩn thận!)
docker compose pull && docker compose up -d --build   # cập nhật
```

## 2. Xem log

```bash
docker compose logs -f collector   # log thu thập + cảnh báo
docker compose logs -f api
docker compose logs -f dashboard
```

## 3. Chạy thu thập thủ công (không chờ lịch)

```bash
docker compose run --rm collector python run.py
```

## 4. Thêm / sửa / tắt nguồn dữ liệu

1. Sửa `sources.json` (đổi `url`, `material`, `prompt`, `enabled`).
2. Áp dụng ngay:
   ```bash
   docker compose restart collector
   docker compose run --rm collector python run.py   # chạy thử
   ```
3. Kiểm tra dashboard có dữ liệu nguồn mới.

> Nếu một nguồn trả **0 dòng giá**: chỉnh `prompt` rõ hơn, kiểm tra trang có hiển thị bảng giá
> công khai không (nhiều site giá nằm sau đăng nhập/trả phí), hoặc trang đã đổi layout.

## 5. Cảnh báo Telegram

- Tạo bot: nhắn **@BotFather** → `/newbot` → lấy `TELEGRAM_BOT_TOKEN`.
- Lấy `chat_id`: nhắn **@userinfobot** (hoặc thêm bot vào nhóm và lấy id nhóm).
- Điền vào `.env`, rồi `docker compose up -d` lại.
- Ngưỡng cảnh báo: `ALERT_THRESHOLD_PCT` (mặc định 2 = báo khi giá đổi > 2% so với kỳ trước).

## 6. Tỉ giá USD→VND

- Mặc định gọi `open.er-api.com` (miễn phí). Khi lỗi mạng → dùng `FX_USD_VND_FALLBACK`.
- Cập nhật tỉ giá dự phòng định kỳ trong `.env` cho khớp thực tế.

## 7. Bảo mật khi mở ra internet

- Đặt `API_TOKEN` (chuỗi bí mật) trong `.env` → API yêu cầu header `X-API-Token`.
  Trên dashboard, mở Console trình duyệt và đặt: `localStorage.setItem('api_token','<token>')`.
- Đặt dashboard sau **reverse proxy + HTTPS** (Caddy/Nginx/Cloudflare) thay vì expose cổng trần.
- Đổi `POSTGRES_PASSWORD` mặc định; không expose cổng 5432 ra ngoài (compose mặc định không expose).

## 8. Sao lưu & phục hồi dữ liệu

```bash
# Backup
docker compose exec db pg_dump -U resin resin > backup_$(date +%F).sql
# Restore
cat backup_YYYY-MM-DD.sql | docker compose exec -T db psql -U resin resin
```

## 9. Xuất báo cáo

- Trên dashboard: nút **Excel** / **CSV**.
- Trực tiếp: `GET http://<host>:8080/api/export.xlsx` (kèm header token nếu bật).

## 10. Sự cố thường gặp

| Triệu chứng | Nguyên nhân | Xử lý |
|-------------|-------------|-------|
| Dashboard trống | Chưa thu thập lần nào | `docker compose run --rm collector python run.py` |
| Collector lỗi `Thieu FIRECRAWL_API_KEY` | Chưa điền key | Điền `FIRECRAWL_API_KEY` trong `.env` |
| API trả 401 | Sai/thiếu token | Đặt `X-API-Token` đúng `API_TOKEN` |
| Một nguồn luôn 0 dòng | Site chặn/đổi layout/giá ẩn | Chỉnh `prompt`, đổi nguồn, kiểm tra ToS |
| Giá VNĐ sai lệch | Tỉ giá fallback cũ | Cập nhật `FX_USD_VND_FALLBACK` |

## 11. Tiêu chí nghiệm thu (Definition of Done)

- [ ] `docker compose up -d` chạy được toàn hệ thống, thu thập theo lịch tự động.
- [ ] Dashboard hiển thị bảng giá hiện tại + biểu đồ xu hướng, lọc theo loại/khu vực, đổi USD↔VNĐ.
- [ ] Export Excel/CSV hoạt động.
- [ ] Cảnh báo Telegram gửi đúng khi biến động > ngưỡng.
- [ ] Lịch sử lưu được, truy xuất nhiều tuần.
- [ ] Đã kiểm tra pháp lý nguồn dữ liệu.
