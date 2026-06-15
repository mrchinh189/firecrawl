# Tài liệu bàn giao — Price Intelligence NVL Masterbatch

Phiên bản 1.0 · Dự án A (điều phối bằng GitHub Actions).

## 1. Hệ thống làm gì
Tự động **cập nhật giá NVL nhựa** (nhựa nền + phụ gia + feedstock dẫn) → **phân tích** (quy đổi
at-sight, spread, dự báo, narrative, cảnh báo) → **báo cáo HTML + DOCX** → **gửi Telegram**, chạy theo
lịch GitHub Actions và kích hoạt theo yêu cầu. Lưu Supabase; ưu tiên thu thập bằng **Firecrawl**.

## 2. Quan trọng — đính chính domain
"NVL" trong dự án = **Nguyên Vật Liệu** (hạt nhựa PP/PE/PS, phụ gia TiO₂/stearic/wax…), KHÔNG phải
cổ phiếu Novaland. Toàn bộ logic xoay quanh giá vốn masterbatch cho khối Mua hàng EUP.

## 3. Luồng xử lý
```
collect/daily.py (Firecrawl→HTTP→Scrapling + ai_extract Claude)
   → db/schema (staging→QC→price_master) [hoặc fixtures offline]
   → analytics/build_analysis.run():  landed(at-sight) + spreads + forecast + narrative + alerts
   → ghi bảng analysis/landed/spreads/forecast (tính 1 lần)
   → report/render.build_view()  (view-model dùng chung)
       ├→ report/build_report.py  (HTML 10 mục)
       ├→ report/build_docx.py    (Word 10 mục, hyperlink + ngày + độ tươi)
       └→ alerts/telegram.py      (text tóm tắt + đính kèm DOCX)
```
**Parity:** DOCX = Web = Telegram vì đều đọc lại từ một view-model, không nơi nào tự tính lại số.

## 4. Bản đồ file (đã build & test)
| File | Vai trò | Test |
|---|---|---|
| `lib.py` | load_yaml, freshness, source_link | test_lib |
| `llm.py` | wrapper Claude fail-soft | (qua narrative) |
| `analytics/landed.py` | quy đổi at-sight tương đương | test_landed |
| `analytics/spreads.py` | spread + chỉ số gốc-100 | test_spreads |
| `forecast/run.py` | baseline + Theil's U | test_forecast |
| `analytics/narrative.py` | 4 đoạn (Claude/template) | test_narrative |
| `alerts/rules.py` | thẻ cảnh báo + đề xuất | test_rules |
| `analytics/build_analysis.py` | orchestrator tính toán | test_integration, test_phase2_data |
| `report/render.py` | view-model dùng chung | test_render |
| `report/build_report.py` | HTML 10 mục | test_build_report |
| `report/build_docx.py` | DOCX 10 mục | test_build_docx |
| `alerts/telegram.py` | text + DOCX (dry-run) | test_telegram |
| `run_pipeline.py` | chạy 1 lần ra 3 kênh | test_pipeline |
| `collect/firecrawl_client.py` | thu thập Firecrawl-first | test_firecrawl_client |

→ **31 test, tất cả xanh**, chạy offline bằng fixtures (không cần khóa).

## 5. Vận hành nhanh
```bash
pip install -r requirements.txt
pytest -q                          # kiểm thử
python fixtures/make_fixtures.py   # dữ liệu mẫu
python run_pipeline.py             # ra báo cáo + telegram dry-run
python collect/daily.py            # thử thu thập thật (cần FIRECRAWL_KEY)
```
Deploy thật: xem `docs/DEPLOY.md`.

## 6. Tinh chỉnh không cần sửa code
- Danh mục NVL & trọng số: `config/materials.yaml`
- Giả định landed/at-sight (thuế NK, cước, lãi vốn): `config/landed.yaml`
- Ngưỡng cảnh báo/dự báo: `config/thresholds.yaml`
- Nguồn & link hiển thị: `config/sources.yaml`, `config/source_links.yaml`
- Model Claude theo khâu: `config/models.yaml`

## 7. Còn lại (Phase 3–4 — đã có spec)
- Web Next.js dashboard (Vercel) + webhook Telegram 2 chiều (`/api/telegram` → repo_dispatch).
- Collectors đầy đủ: `collect/history.py` (EIA/FRED/Comtrade/World Bank backfill 3–5 năm), `collect/news.py`.
- Phase 4: Scrapling nâng cao + Claude commentary/news sâu hơn + nới QC cho chuỗi index.
- Spec chi tiết: `tài liệu gốc/docs/superpowers/` (đã kèm trong gói bàn giao của bạn).

## 8. Giới hạn đã biết
- Nguồn cào công khai có thể đổi layout/chặn IP → đã dùng AI-extract + fail-soft + nhiều fallback.
- Dự báo dùng chuỗi ngắn (fixtures 12 tuần) → độ tin cậy "thấp/vừa"; cần `collect/history.py` để backfill.
- ⛔ Không cào nguồn bản quyền (ICIS/Platts/Argus/ChemOrbis) — nhập qua form.

## 9. Vị trí
Thư mục `price-intel/` tự chứa — tách sang repo riêng `price-intel` để dùng GitHub Actions
(`cp -r price-intel ~/price-intel`). Không phụ thuộc phần còn lại của monorepo Firecrawl.
