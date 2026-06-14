# 📊 Price Intelligence — NVL Masterbatch (EUP Group)

Hệ thống **thu thập → phân tích → báo cáo giá nguyên vật liệu (NVL) nhựa masterbatch**:
nhựa nền (PP/PE/HDPE/PS) + phụ gia (TiO₂, PE wax, base oil, stearic, zinc stearate, carbon black…)
và feedstock dẫn (Brent/naphtha/ethylene/propylene). Tự động bằng GitHub Actions cron, lưu Supabase,
xuất **báo cáo HTML + DOCX (10 mục)** và đẩy **Telegram**. Dự báo 6 tuần + cảnh báo quyết định.

> ⚠️ **NVL = Nguyên Vật Liệu** (hạt nhựa/phụ gia), KHÔNG phải cổ phiếu.
> Báo cáo mang tính tham khảo, không phải khuyến nghị đầu tư/mua hàng.

## Điểm cốt lõi

| Tính năng | Mô tả |
|---|---|
| **Thu thập ưu tiên Firecrawl** | Firecrawl (JS+chống chặn) → HTTP → Scrapling; AI-extract bằng Claude. Xem `docs/FIRECRAWL.md` |
| Quy đổi **at-sight tương đương** | Chuẩn hóa USD/tấn → landed VND/kg → trừ usance → so công bằng giữa nguồn khác điều khoản |
| Spread/leading indicators | naphtha–ethylene, PP–propylene, ethylene–PE; chỉ số gốc-100 (phân kỳ resin↓ vs phụ gia↑) |
| Dự báo 6 tuần | naive/MA tự hạ cấp theo độ dài chuỗi + Theil's U + độ tin cậy + cơ sở |
| Narrative + cảnh báo | 4 đoạn phân tích (Claude, fallback template) + thẻ {MUA/THEO_DÕI/PHÂN_KỲ/CHỜ} |
| Báo cáo | HTML 10 mục + DOCX (hyperlink nguồn, ngày giá, độ tươi 🟢🟡🔴) — **DOCX = Web = Telegram** |
| Telegram | Text tóm tắt (link+ngày+tin) + đính kèm DOCX. Dry-run an toàn khi thiếu token |
| Lưu trữ | Supabase Postgres; **chế độ fixtures** chạy offline không cần khóa |

## Chạy demo offline (KHÔNG cần khóa)

```bash
pip install -r requirements.txt
python fixtures/make_fixtures.py     # sinh dữ liệu mẫu 12 tuần
python run_pipeline.py               # -> data/report.html + data/bao_cao_phan_tich.docx + telegram dry-run
pytest -q                            # 31 test xanh
```

## Cấu trúc

```
config/        materials, landed, source_links, thresholds, sources, models (.yaml)
lib.py         helper: load_yaml, freshness 🟢🟡🔴, source_link
llm.py         wrapper Claude fail-soft (prompt caching)
collect/       common, firecrawl_client (FIRECRAWL-first), daily (orchestrator)
analytics/     landed (at-sight), spreads, narrative, store, build_analysis
forecast/      run (baseline + Theil's U)
alerts/        rules (thẻ cảnh báo), telegram (text + DOCX)
report/        render (view-model), build_report (HTML), build_docx (Word)
db/schema.sql  Supabase (idempotent)
fixtures/      dữ liệu mẫu offline
.github/workflows/  update + weekly (kích hoạt khi price-intel/ là gốc repo riêng)
```

## Triển khai thật

Xem **[docs/DEPLOY.md](docs/DEPLOY.md)** (khóa, Supabase, GitHub Actions, Telegram) ·
**[docs/HANDOVER.md](docs/HANDOVER.md)** (bàn giao) · **[docs/FIRECRAWL.md](docs/FIRECRAWL.md)** (vì sao ưu tiên Firecrawl).

## Trạng thái

- ✅ Phase 1 (lõi tính toán) + Phase 2 (báo cáo HTML/DOCX/Telegram) — chạy offline, 31 test xanh.
- ✅ Lớp thu thập Firecrawl-first + orchestrator (fail-soft).
- 🔜 Phase 3: web Next.js (Vercel) + webhook Telegram 2 chiều + collectors history/news đầy đủ.
- 🔜 Phase 4: Scrapling fallback nâng cao + Claude commentary/news sâu hơn.
