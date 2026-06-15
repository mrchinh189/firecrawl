# Vì sao ưu tiên Firecrawl (và cơ chế fallback)

Theo yêu cầu: **ưu tiên Firecrawl, chỉ dùng chức năng khác khi Firecrawl không có/được**.
Đây là điểm khác có chủ đích so với kế hoạch gốc (Phase 4) vốn đặt Scrapling làm chính.

## Thứ tự thu thập (trong `collect/firecrawl_client.py`)

```
scrape_md(url):
  1) Firecrawl API   (FIRECRAWL_KEY)   ← CHÍNH: render JS, chống chặn, ổn định nhất
  2) HTTP thuần      (requests)        ← fallback: trang tĩnh, không JS
  3) Scrapling stealth (nếu đã cài)    ← fallback cuối
  -> None nếu hết cách (fail-soft, KHÔNG gãy pipeline)
```

Đổi thứ tự bằng env `FETCH_PREFER=firecrawl|http`. Sau khi có markdown,
`ai_extract()` dùng **Claude** bóc số theo schema JSON (không vỡ khi web đổi layout).

## Vì sao Firecrawl là lựa chọn chính

- Nhiều nguồn (ThePlasticsExchange, DCE, Polymerupdate, businessanalytiq, MPOB) **chặn IP cloud**
  hoặc cần **JS render** → HTTP thuần thường nhận 403 (đã kiểm chứng khi demo).
- Firecrawl xử lý JS + xoay IP + trả markdown sạch → tỉ lệ thành công cao nhất khi chạy trong CI.
- Vẫn giữ HTTP + Scrapling làm lưới an toàn để không phụ thuộc 100% vào 1 dịch vụ.

## Khóa cần

`FIRECRAWL_KEY` lấy ở https://firecrawl.dev (gói free ~500 credits). Thiếu khóa →
tự rơi xuống HTTP/Scrapling; nếu vẫn fail → nguồn đó bị SKIP (báo cáo dùng các nguồn còn lại).

## ⛔ Không cào (bản quyền/paywall)

ICIS · Platts · Argus · Fastmarkets · ChemOrbis · Polymerupdate (bản trả phí) · Wood Mackenzie.
→ Nhập qua form/PDF circular nhà sản xuất. Danh sách trong `config/sources.yaml` mục `blocked`.
