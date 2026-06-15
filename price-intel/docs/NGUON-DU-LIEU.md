# Nguồn dữ liệu giá NVL — đã kiểm chứng (cập nhật 2026-06)

Mình (Claude) đã tự khảo sát & kiểm chứng các nguồn MIỄN PHÍ cho từng nhóm NVL.
Kết luận quan trọng: **nhiều nguồn chặn HTTP thường (403) → BẮT BUỘC dùng Firecrawl** (đúng kiến trúc đã chọn).

## ✅ Tầng FREE — API/JSON (không cần Firecrawl)

| Nhóm | Nguồn | Endpoint (đã xác nhận) | Khóa |
|---|---|---|---|
| Brent (feedstock dẫn) | EIA RBRTE | `https://api.eia.gov/v2/petroleum/pri/spt/data/?facets[series][]=RBRTE&frequency=daily` | `EIA_KEY` (free) |
| USD/VND | Vietcombank API JSON | `https://www.vietcombank.com.vn/api/exchangerates?date=YYYY-MM-DD` (field `Data[].currencyCode=USD`, `sell`) | không |
| USD/VND (fallback) | VNAppMob (mirror VCB) | `https://vapi.vnappmob.com/api/v2/exchange_rate/vcb` | không |
| Backfill PP/PE | FRED `PCU325211325211`, `PCU3252113252111` (PPI nhựa/resin, 1976→) | `https://api.stlouisfed.org/fred/series/observations?series_id=...` | `FRED_API_KEY` (free) |
| Backfill phụ gia | FRED `PPOILUSDM` (Global Palm Oil USD/MT — driver stearic/wax/zinc/calcium stearate) | nt | `FRED_API_KEY` |
| Backfill Brent dài | FRED `POILBREUSDM` | nt | `FRED_API_KEY` |
| Unit value NK | UN Comtrade (HS 3901/3902/3903) | `https://comtradeapi.un.org/...` | `COMTRADE_KEY` (free) |

> ⚠️ Bản XML cũ của Vietcombank (`portal.../pXML.aspx`) **trả 403 với IP cloud** (đã test) → đã chuyển sang API JSON ở trên; nếu vẫn chặn, cho qua Firecrawl.

## 🔥 Tầng FIRECRAWL — đã xác nhận chặn HTTP thường (cần Firecrawl)

| Nhóm | Nguồn (URL cụ thể từng mã) | Ghi chú |
|---|---|---|
| PP | `businessanalytiq.com/procurementanalytics/index/polypropylene-price-index/` | **403 với HTTP thường** → Firecrawl. Index US$/MT nhiều vùng |
| PE/HDPE | `.../polyethylene-price-index/` | nt |
| Propylene | `.../propylene-price-index/` | nt |
| Stearic acid | `.../stearic-acid-price-index/` | nt (Europe ~US$2.12/kg tại thời điểm khảo sát) |
| TiO₂ (TQ) | `.../titanium-dioxide-tio2-china-price-index/` | nt — TiO₂ China sát bối cảnh cost-push |
| PP/PE CFR SEA | `polymerupdate.com/prices/sea/polymers/pp` (và `/pe`) | CFR Đông Nam Á **gồm Việt Nam**, nhiều grade (raffia/inj/film), free headline → Firecrawl |
| PP/PE spot Mỹ | `theplasticsexchange.com` | ¢/lb → Firecrawl |
| PP futures | `dce.com.cn/.../marketdata` | RMB/tấn, JS → Firecrawl |

→ Sau khi Firecrawl trả markdown, `firecrawl_client.ai_extract()` dùng Claude bóc số theo schema, rồi `collect/normalize.py` chuẩn hóa về `price_master`.

## 🆕 Nguồn bổ sung (bạn cung cấp — đã research 2026-06)

Đều **chặn HTTP thường (403, đã test)** → vào qua Firecrawl. Là **driver** cho phụ gia oleochemical/kẽm.

| Nguồn | URL | Dữ liệu | Map driver |
|---|---|---|---|
| **MPOC** | `mpoc.org.my/market-insight/daily-palm-oil-prices/` | Giá dầu cọ ngày (CPO/RBD palm olein, RM/MT) | `palm_oil` → stearic, PE wax, zinc/calcium stearate |
| **Investing FCPO** | `investing.com/commodities/malaysian-crude-palm-oil-futures-historical-data` | Futures dầu cọ Bursa (MYR/MT, hợp đồng 25t), lịch sử free | `palm_oil` (futures — leading) |
| **LME Zinc** | `lme.com/en/Metals/Non-ferrous/LME-Zinc` | Giá kẽm **day-delayed** free (USD/t) | `lme_zinc` → zinc stearate |
| **SCI99** | `intl.sci99.com` | Giá hóa chất/nhựa/TiO₂/oleochemical TQ | tio2, stearic — ⚠️ **CẦN ĐĂNG KÝ/TRẢ PHÍ**, chỉ bóc phần free |

**Nguồn dầu cọ thay thế KHÔNG chặn (free, có thể tải thẳng):**
- MPOB daily: `bepi.mpob.gov.my/index.php/price/daily` (đã có trong sources)
- IndexMundi palm oil monthly MYR (CSV/chart free): `indexmundi.com/commodities/?commodity=palm-oil&currency=myr`
- FRED `PPOILUSDM` (đã dùng cho backfill — không cần Firecrawl)

→ Đã thêm `palm_oil` + `lme_zinc` vào `materials.yaml` (feedstock/driver) và gán làm `price_sources` cho
stearic/pe_wax/zinc_st/ca_st. `normalize.py` nhận diện palm oil/CPO/FCPO/zinc. forecast dùng làm
**proxy driver** khi phụ gia thiếu giá tuyệt đối (gắn cờ độ tin cậy "thấp").

> 💡 Lưu ý SCI99: là dịch vụ trả phí (4M user, nhiều khách Fortune 500). Nếu bạn có tài khoản, có thể
> thêm credential/cookie cho Firecrawl; nếu không, ưu tiên MPOC/MPOB/businessanalytiq cho TiO₂/stearic.

## ⛔ KHÔNG cào (bản quyền/paywall — đã xác nhận)

ICIS · S&P Global Platts (kể cả "CFR Vietnam PE/PP assessments" mới) · Argus · ChemOrbis ·
Fastmarkets · Intratec · IndexBox · Wood Mackenzie. → Mua license rồi NHẬP QUA FORM, hoặc đọc PDF circular nhà sản xuất (SABIC/Exxon/Dow/Borouge/Formosa/**LSP Long Sơn**).

## Cách dùng
- Cập nhật danh sách trong `config/sources.yaml` (đã điền URL cụ thể ở trên).
- Cắm `FIRECRAWL_KEY` → nhánh Firecrawl chạy cho businessanalytiq/Polymerupdate/TPE/DCE.
- Cắm `EIA_KEY`/`FRED_API_KEY`/`COMTRADE_KEY` → các nguồn FREE chạy.
- Vietcombank chạy ngay (không cần khóa).

## Nguồn tham khảo khảo sát
- EIA Open Data: https://www.eia.gov/opendata/ · RBRTE browser: https://www.eia.gov/opendata/browser/petroleum/pri/spt
- businessanalytiq: https://businessanalytiq.com/procurementanalytics/index/polypropylene-price-index/ · https://businessanalytiq.com/procurementanalytics/index/titanium-dioxide-tio2-china-price-index/
- FRED: https://fred.stlouisfed.org/series/PCU325211325211 · https://fred.stlouisfed.org/series/PPOILUSDM
- Vietcombank API (qua TM DEV): https://huynhtanmao.com/huong-dan-lay-ti-gia-tu-api-ngan-hang-vietcombank/ · VNAppMob: https://vapi.vnappmob.com/
- Polymerupdate SEA: https://polymerupdate.com/prices/sea/polymers/pp
