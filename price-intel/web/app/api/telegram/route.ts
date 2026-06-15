import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

// Webhook Telegram 2 chiều. Vercel chỉ làm "chuông cửa": xác thực + bấm GitHub repo_dispatch
// cho lệnh nặng (/capnhat); lệnh nhẹ (/gia, /dubao) trả ngay từ Supabase.
// Đặt webhook: https://api.telegram.org/bot<token>/setWebhook?url=<vercel>/api/telegram&secret_token=<secret>

async function tgSend(chatId: number, text: string) {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  if (!token) return;
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: "HTML", disable_web_page_preview: true }),
  });
}

async function repoDispatch(): Promise<boolean> {
  const { GH_DISPATCH_PAT, GH_OWNER, GH_REPO } = process.env;
  if (!GH_DISPATCH_PAT || !GH_OWNER || !GH_REPO) return false;
  const r = await fetch(`https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${GH_DISPATCH_PAT}`,
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ event_type: "telegram-update" }),
  });
  return r.ok;
}

async function latestDashboard(): Promise<any | null> {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null;
  const sb = createClient(url, key);
  const { data } = await sb.from("analysis").select("payload").eq("kind", "dashboard")
    .order("run_date", { ascending: false }).limit(1).single();
  return data?.payload ?? null;
}

const HELP =
  "🤖 Lệnh: /capnhat (chạy cập nhật) · /gia &lt;mã&gt; · /dubao · /baocao · /help";

export async function POST(req: NextRequest) {
  // Xác thực secret token (Telegram gửi qua header)
  const secret = process.env.TELEGRAM_WEBHOOK_SECRET;
  if (secret && req.headers.get("x-telegram-bot-api-secret-token") !== secret) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }
  const update = await req.json().catch(() => ({}));
  const msg = update?.message;
  if (!msg?.text) return NextResponse.json({ ok: true });

  const chatId = msg.chat.id as number;
  const [cmdRaw, ...args] = (msg.text as string).trim().split(/\s+/);
  const cmd = cmdRaw.replace(/@.*$/, "").toLowerCase();

  if (cmd === "/help" || cmd === "/start") {
    await tgSend(chatId, HELP);
  } else if (cmd === "/capnhat" || cmd === "/update") {
    const ok = await repoDispatch();
    await tgSend(chatId, ok
      ? "⏳ Đã kích hoạt cập nhật (GitHub Actions). Báo cáo sẽ gửi khi xong."
      : "⚠️ Chưa cấu hình GH_DISPATCH_PAT/GH_OWNER/GH_REPO trên Vercel.");
  } else if (cmd === "/gia" || cmd === "/price") {
    const dash = await latestDashboard();
    const q = (args[0] || "pp").toLowerCase();
    const card = dash?.kpi?.find((c: any) => c.key === q);
    await tgSend(chatId, card
      ? `📊 <b>${card.label}</b>: ${card.value}${card.chg != null ? ` (${card.chg > 0 ? "▲+" : "▼"}${Math.abs(card.chg)}%)` : ""}${card.landed ? ` · landed ${card.landed}` : ""} · ${card.date ?? ""}`
      : `Không có dữ liệu cho "${q}". Thử: pp, pe, tio2, stearic, brent.`);
  } else if (cmd === "/dubao" || cmd === "/forecast") {
    const dash = await latestDashboard();
    const fc = dash?.forecast?.pp;
    if (fc) {
      const rows = fc.rows.map((r: any) => `T+${r.week}: ${r.yhat.toLocaleString("vi-VN")}`).join("\n");
      await tgSend(chatId, `📈 <b>Dự báo PP 6 tuần</b> (${fc.meta.model}, tin cậy ${fc.meta.confidence})\n${rows}`);
    } else {
      await tgSend(chatId, "Chưa có dữ liệu dự báo (cần chạy pipeline trước).");
    }
  } else if (cmd === "/baocao" || cmd === "/report") {
    const base = process.env.DASHBOARD_URL || "";
    await tgSend(chatId, base ? `🖥 Dashboard: ${base}` : "Chưa cấu hình DASHBOARD_URL.");
  } else {
    await tgSend(chatId, HELP);
  }
  return NextResponse.json({ ok: true });
}

export async function GET() {
  return NextResponse.json({ ok: true, service: "price-intel telegram webhook" });
}
