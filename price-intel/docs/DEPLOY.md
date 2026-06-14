# Hướng dẫn triển khai (Dự án A — GitHub Actions)

## 1. Tách thành repo riêng
Dự án này tự chứa trong thư mục `price-intel/`. Để dùng GitHub Actions cron, copy thư mục này
thành **gốc của một repo mới** (vd `price-intel`), khi đó `.github/workflows/*.yml` mới kích hoạt.

```bash
cp -r price-intel ~/price-intel && cd ~/price-intel
git init && git add -A && git commit -m "init price-intel"
gh repo create price-intel --private --source=. --push
```

## 2. Bảy nhóm khóa (đặt bằng GitHub Secrets — KHÔNG commit)

| Khóa | Lấy ở | Bắt buộc? |
|---|---|---|
| `FIRECRAWL_KEY` | firecrawl.dev | Khuyến nghị (nguồn cào chính) |
| `EIA_KEY` | eia.gov/opendata | Tùy (Brent) |
| `COMTRADE_KEY` | comtradeplus.un.org | Tùy (unit value NK) |
| `FRED_API_KEY` | fred.stlouisfed.org | Tùy (backfill) |
| `ANTHROPIC_API_KEY` | console.anthropic.com | Tùy (narrative Claude; thiếu → template) |
| `SUPABASE_DB_URL` | supabase.com → Database | Tùy (thiếu → fixtures) |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | @BotFather / @userinfobot | Tùy (đẩy báo cáo) |

> Fail-soft: thiếu khóa nào, nguồn/bước đó tự SKIP — pipeline KHÔNG gãy.

```bash
gh secret set FIRECRAWL_KEY -b "..."   # lặp cho từng khóa, hoặc: gh secret set -f .env
```

## 3. Supabase (lưu trữ)
```bash
psql "$SUPABASE_DB_URL" -f db/schema.sql   # tạo bảng (idempotent, chạy lại an toàn)
```

## 4. Lịch tự động + chạy tay
- **Lịch:** `.github/workflows/weekly.yml` (mặc định 02:00 UTC thứ Tư). Đổi cron tùy ý.
- **Chạy tay:** tab Actions → `update` → Run workflow. Hoặc `gh workflow run update`.
- **Theo yêu cầu (2 chiều):** webhook Telegram → `repo_dispatch (telegram-update)` → workflow `update`
  (phần webhook trên Vercel thuộc Phase 3).

## 5. Telegram
1. Tạo bot qua @BotFather → `TELEGRAM_BOT_TOKEN`. Lấy `TELEGRAM_CHAT_ID` qua @userinfobot.
2. Mỗi lần chạy `run_pipeline.py` sẽ gửi text tóm tắt + đính kèm DOCX. Thiếu token → dry-run (in ra log).

## 6. Vercel (Phase 3 — tùy chọn)
Dashboard Next.js đọc Supabase + webhook `/api/telegram` → `repo_dispatch`. Sẽ bổ sung ở Phase 3
(spec đã thiết kế trong `docs/superpowers/specs/...`). Backend hiện tại đã sẵn sàng cấp dữ liệu.

## 7. Kiểm thử trước khi deploy
```bash
pip install -r requirements.txt
pytest -q                 # 31 test
python run_pipeline.py    # sinh report.html + DOCX + telegram dry-run
```
