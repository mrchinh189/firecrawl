#!/usr/bin/env bash
# setup.sh — tự động hóa các bước deploy price-intel (Dự án A: GitHub Actions + Vercel + Supabase).
# Chạy trên MÁY CỦA BẠN (cần đăng nhập gh/khóa của bạn). KHÔNG commit .env.
# Dùng: bash setup.sh            (chạy đủ các bước, hỏi xác nhận từng việc rủi ro)
#       bash setup.sh --check    (chỉ kiểm tra điều kiện, không thay đổi gì)
set -uo pipefail
cd "$(dirname "$0")"

GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; NC='\033[0m'
ok(){ echo -e "${GREEN}✓${NC} $*"; }
warn(){ echo -e "${YELLOW}!${NC} $*"; }
err(){ echo -e "${RED}✗${NC} $*"; }
ask(){ read -r -p "$(echo -e "${YELLOW}? $* [y/N] ${NC}")" a; [[ "$a" =~ ^[Yy]$ ]]; }

CHECK_ONLY=false; [[ "${1:-}" == "--check" ]] && CHECK_ONLY=true

echo "=== Price-Intel · Setup deploy ==="

# 1) Công cụ
for t in python3 pip3; do command -v $t >/dev/null && ok "$t" || { err "thiếu $t"; exit 1; }; done
command -v node >/dev/null && ok "node $(node -v)" || warn "thiếu node (cần cho web/)"
command -v gh   >/dev/null && ok "gh CLI"          || warn "thiếu gh (bỏ qua bước set secrets)"
command -v psql >/dev/null && ok "psql"            || warn "thiếu psql (bỏ qua bước chạy schema)"

# 2) Tạo .env từ mẫu
[[ -f .env ]] || { cp .env.example .env; warn ".env vừa tạo từ mẫu — HÃY ĐIỀN KHÓA rồi chạy lại."; }
[[ -f web/.env.local ]] || cp web/.env.local.example web/.env.local
ok ".env / web/.env.local sẵn sàng"
set -a; source .env 2>/dev/null || true; set +a

$CHECK_ONLY && { echo "--- chỉ kiểm tra, dừng ---"; exit 0; }

# 3) Cài deps + test + smoke pipeline (offline, không cần khóa)
ask "Cài dependencies + chạy test + sinh báo cáo mẫu?" && {
  pip3 install -q -r requirements.txt && ok "đã cài deps"
  python3 fixtures/make_fixtures.py >/dev/null && ok "fixtures"
  python3 -m pytest -q && ok "tests xanh"
  python3 run_pipeline.py >/dev/null 2>&1 && ok "đã sinh data/report.html + DOCX"
}

# 4) Supabase schema
if [[ -n "${SUPABASE_DB_URL:-}" ]] && command -v psql >/dev/null; then
  ask "Chạy db/schema.sql lên Supabase?" && { psql "$SUPABASE_DB_URL" -f db/schema.sql && ok "schema áp dụng"; }
else warn "Bỏ qua schema (thiếu SUPABASE_DB_URL hoặc psql)"; fi

# 5) GitHub secrets từ .env
if command -v gh >/dev/null; then
  ask "Đẩy các khóa trong .env lên GitHub Secrets (repo hiện tại)?" && {
    gh secret set -f .env && ok "đã set secrets"
  }
else warn "Bỏ qua set secrets (thiếu gh)"; fi

# 6) Telegram setWebhook (nếu đã deploy Vercel)
if [[ -n "${TELEGRAM_BOT_TOKEN:-}" && -n "${DASHBOARD_URL:-}" && -n "${TELEGRAM_WEBHOOK_SECRET:-}" ]]; then
  ask "Đăng ký webhook Telegram tới ${DASHBOARD_URL}/api/telegram?" && {
    curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${DASHBOARD_URL}/api/telegram&secret_token=${TELEGRAM_WEBHOOK_SECRET}" && echo && ok "webhook đăng ký"
  }
else warn "Bỏ qua webhook (thiếu TELEGRAM_BOT_TOKEN/DASHBOARD_URL/TELEGRAM_WEBHOOK_SECRET)"; fi

echo
ok "Hoàn tất. Bước thủ công còn lại: tách price-intel/ thành repo riêng + import 'web/' vào Vercel."
echo "Chi tiết: docs/DEPLOY.md"
