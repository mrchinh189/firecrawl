# Web Dashboard — Price Intelligence NVL (Next.js + Vercel)

Dashboard đọc **view-model do pipeline Python ghi vào Supabase** (bảng `analysis`, `kind='dashboard'`),
hiển thị đủ 10 mục như báo cáo DOCX (parity **Web = DOCX = Telegram**). Kèm **webhook Telegram 2 chiều**.

Web KHÔNG tự tính lại số — chỉ đọc & trình bày.

## Chạy local
```bash
cd web
cp .env.local.example .env.local     # điền Supabase (hoặc để trống -> dùng mock data)
npm install
npm run dev                          # http://localhost:3000
```
Thiếu `NEXT_PUBLIC_SUPABASE_URL/ANON_KEY` → dashboard tự dùng **mock data** (sinh từ view-model Python) để demo.

## Deploy Vercel
1. Import repo vào Vercel, **Root Directory = `web`**.
2. Đặt env (Settings → Environment Variables): `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`,
   `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `GH_DISPATCH_PAT`, `GH_OWNER`, `GH_REPO`, `DASHBOARD_URL`.
3. Deploy → Vercel tự build. Dashboard cập nhật live theo Supabase (pipeline ghi → web đọc).

## Webhook Telegram 2 chiều
Sau khi deploy, đăng ký webhook (1 lần):
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<app>.vercel.app/api/telegram&secret_token=<SECRET>"
```
Lệnh: `/capnhat` (→ GitHub repo_dispatch chạy pipeline) · `/gia pp` · `/dubao` · `/baocao` · `/help`.
Lệnh nặng (`/capnhat`) đẩy sang GitHub Actions vì Vercel function có giới hạn thời gian; lệnh nhẹ trả ngay từ Supabase.

## Cấu trúc
```
app/page.tsx            dashboard 10 mục (RSC)
app/api/telegram/route.ts  webhook 2 chiều -> repo_dispatch
lib/data.ts             đọc Supabase (analysis kind='dashboard') -> fallback mock
lib/mock.ts             mock data sinh từ view-model Python
lib/{types,format}.ts   kiểu + định dạng VND/độ tươi
```
