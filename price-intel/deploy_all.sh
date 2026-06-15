#!/usr/bin/env bash
# deploy_all.sh — DEPLOY TRỌN GÓI 1 LỆNH (chạy trên MÁY CỦA BẠN, nơi egress mở).
# Làm tự động: tạo repo riêng -> push -> GitHub secrets -> Supabase schema ->
#              Vercel (web) -> Telegram webhook -> chạy pipeline lần đầu.
# Yêu cầu: đã đăng nhập `gh auth login`; có node/npm, python3, psql; đã điền .env.
#
# Dùng:  cp .env.example .env   # điền đầy đủ khóa (xem danh sách bên dưới)
#        bash deploy_all.sh
set -uo pipefail
cd "$(dirname "$0")"
G='\033[0;32m'; Y='\033[0;33m'; R='\033[0;31m'; N='\033[0m'
ok(){ echo -e "${G}✓${N} $*"; } ; warn(){ echo -e "${Y}!${N} $*"; } ; die(){ echo -e "${R}✗ $*${N}"; exit 1; }
need(){ command -v "$1" >/dev/null || die "thiếu '$1' — cài rồi chạy lại"; }
ask(){ read -r -p "$(echo -e "${Y}? $* [Y/n] ${N}")" a; [[ -z "$a" || "$a" =~ ^[Yy]$ ]]; }

REPO_NAME="${REPO_NAME:-price-intel}"

echo "=== DEPLOY TRỌN GÓI price-intel ==="
need git; need python3; need pip3
[[ -f .env ]] || die ".env chưa có — chạy: cp .env.example .env rồi điền khóa"
set -a; source .env; set +a

# ---- Kiểm tra khóa tối thiểu ----
miss=()
for k in FIRECRAWL_KEY ANTHROPIC_API_KEY; do [[ -n "${!k:-}" ]] || miss+=("$k"); done
[[ ${#miss[@]} -gt 0 ]] && warn "Thiếu khóa (sẽ SKIP nguồn liên quan): ${miss[*]}"
for k in SUPABASE_DB_URL NEXT_PUBLIC_SUPABASE_URL NEXT_PUBLIC_SUPABASE_ANON_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID; do
  [[ -n "${!k:-}" ]] || warn "Chưa có $k (một số bước sẽ bỏ qua)"
done

# ---- 1) Test + sinh báo cáo offline ----
ask "B1. Cài deps + test + sinh báo cáo mẫu?" && {
  pip3 install -q -r requirements.txt && python3 fixtures/make_fixtures.py >/dev/null
  python3 -m pytest -q && ok "tests xanh"
  python3 run_pipeline.py >/dev/null 2>&1 && ok "đã sinh data/report.html + DOCX"
}

# ---- 2) Tạo repo riêng + push ----
if command -v gh >/dev/null && ask "B2. Tạo repo GitHub '$REPO_NAME' (private) và push?"; then
  [[ -d .git ]] || { git init -q && git add -A && git commit -qm "init price-intel"; }
  gh repo create "$REPO_NAME" --private --source=. --push 2>/dev/null && ok "đã tạo+push $REPO_NAME" \
    || { git add -A && git commit -qm "update" 2>/dev/null; git push -u origin HEAD 2>/dev/null && ok "đã push"; }
else warn "Bỏ qua tạo repo (thiếu gh hoặc bạn chọn no)"; fi

# ---- 3) GitHub Secrets ----
if command -v gh >/dev/null && ask "B3. Đẩy khóa .env lên GitHub Secrets?"; then
  gh secret set -f .env && ok "secrets đã set"
fi

# ---- 4) Supabase schema ----
if [[ -n "${SUPABASE_DB_URL:-}" ]] && command -v psql >/dev/null && ask "B4. Chạy schema lên Supabase?"; then
  psql "$SUPABASE_DB_URL" -f db/schema.sql && ok "schema áp dụng"
else warn "Bỏ qua schema (thiếu SUPABASE_DB_URL/psql)"; fi

# ---- 5) Vercel deploy web ----
if ask "B5. Deploy web/ lên Vercel?"; then
  command -v vercel >/dev/null || { npm i -g vercel && ok "đã cài vercel CLI"; }
  ( cd web && npm install --silent
    # đẩy env cho Vercel (production)
    for k in NEXT_PUBLIC_SUPABASE_URL NEXT_PUBLIC_SUPABASE_ANON_KEY TELEGRAM_BOT_TOKEN TELEGRAM_WEBHOOK_SECRET GH_DISPATCH_PAT GH_OWNER GH_REPO DASHBOARD_URL; do
      [[ -n "${!k:-}" ]] && printf '%s' "${!k}" | vercel env add "$k" production --force >/dev/null 2>&1 || true
    done
    vercel deploy --prod --yes ) && ok "web đã deploy (xem URL ở trên)"
else warn "Bỏ qua Vercel"; fi

# ---- 6) Telegram webhook ----
if [[ -n "${TELEGRAM_BOT_TOKEN:-}" && -n "${DASHBOARD_URL:-}" && -n "${TELEGRAM_WEBHOOK_SECRET:-}" ]] && ask "B6. Đăng ký Telegram webhook?"; then
  curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${DASHBOARD_URL}/api/telegram&secret_token=${TELEGRAM_WEBHOOK_SECRET}" && echo && ok "webhook đăng ký"
else warn "Bỏ qua webhook (thiếu DASHBOARD_URL/TELEGRAM_WEBHOOK_SECRET — quay lại sau khi có URL Vercel)"; fi

# ---- 7) Chạy pipeline thật lần đầu (collect -> báo cáo -> Telegram) ----
if ask "B7. Chạy thu thập giá THẬT + báo cáo + gửi Telegram ngay?"; then
  python3 collect/free.py || true
  python3 collect/daily.py || true
  python3 collect/news.py || true
  python3 db/load.py || true
  python3 run_pipeline.py && ok "đã chạy pipeline thật"
fi

echo; ok "XONG. Lịch tự động (GitHub Actions weekly) sẽ tự chạy; hoặc nhắn bot /capnhat."
echo "Nếu B5 mới có URL Vercel: đặt DASHBOARD_URL=<url> vào .env rồi chạy lại để làm B6 (webhook)."
