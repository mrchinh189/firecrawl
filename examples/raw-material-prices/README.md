# Cào giá nguyên vật liệu (NVL) bằng Firecrawl

Script lấy giá NVL hằng ngày từ nhiều nguồn và ghi vào file CSV lịch sử.

| Source key | NVL | Nguồn | Đơn vị | Cách lấy |
| --- | --- | --- | --- | --- |
| `investing_cpo` | Dầu cọ thô Malaysia (CPOc1) | vn.investing.com | USD/tấn | markdown, fallback sang thẻ meta `LAST_PRICE` |
| `100ppi_sulfuric_acid` | Axit sunfuric (硫酸) | m1.100ppi.com | CNY/tấn | bảng 日期/价格/日涨跌, bỏ qua ngày chưa công bố |
| `mpoc_cpo` | CPO, giá thanh toán Bursa | mpoc.org.my | MYR/tấn | bảng "CPO Prices", lấy dòng mới nhất |
| `lme_zinc` | Kẽm LME, giá đóng cửa 3 tháng | lme.com | USD/tấn | chờ JS render (`wait_for=12000`), lấy toàn trang |

## Cách hoạt động

1. **Scrape**: `Firecrawl.scrape(url, formats=["markdown"], max_age=0, ...)`.
   `max_age=0` bắt Firecrawl lấy bản mới thay vì dùng cache.
2. **Parse bằng regex**: mỗi nguồn có một hàm parse riêng, không tốn credit LLM và cho ra
   kết quả giống nhau giữa các lần chạy.
3. **Fallback bằng LLM**: nếu trang đổi giao diện và parser không đọc được, script gọi lại với
   `formats=[{"type": "json", "schema": ..., "prompt": ...}]` để Firecrawl tự trích xuất giá.
   Cột `method` trong CSV ghi `llm` để bạn biết parser cần sửa. Dùng `--no-llm` để tắt fallback này.
4. **Lưu trữ**: ghi nối vào `prices.csv` và bỏ qua bản ghi trùng `(source, price_date, price)`,
   nên chạy nhiều lần trong ngày cũng không bị nhân đôi dữ liệu.

## Chạy

```bash
pip install -r requirements.txt
export FIRECRAWL_API_KEY=fc-...
# Nếu tự host Firecrawl: export FIRECRAWL_API_URL=http://localhost:3002

python scrape_prices.py
python scrape_prices.py --only lme_zinc mpoc_cpo
```

Ví dụ kết quả:

```
Dầu cọ thô Malaysia (CPO futures, CPOc1)               1,121.25 USD/tấn    -0.47%  (2026-10-02)
Axit sunfuric (硫酸) - giá cơ sở 生意社                 1,710.00 CNY/tấn    +0.00%  (2026-10-03)
Dầu cọ thô (CPO) - giá thanh toán Bursa Malaysia       4,554.00 MYR/tấn    -1.21%  (2026-10-01)
Kẽm LME (3-month closing, day-delayed)                 3,710.50 USD/tấn    -0.36%  (2026-10-02)
```

Test cho các parser chạy offline, dùng markdown thật mà Firecrawl đã trả về:

```bash
python -m pytest test_parsers.py
```

## Thêm NVL mới

Thêm một `Source(...)` vào `SOURCES` trong `scrape_prices.py`:

```python
Source(
    key="lme_copper",
    material="Đồng LME (3-month closing)",
    url="https://www.lme.com/en/Metals/Non-ferrous/LME-Copper",
    unit="USD/tấn",
    parser=parse_lme,  # cùng giao diện LME nên dùng lại được parser
    scrape_options={"only_main_content": False, "wait_for": 12000},
),
```

Với một trang hoàn toàn mới, cách nhanh nhất là để `parser` là một hàm luôn `raise ValueError`
để dùng fallback LLM, xem markdown Firecrawl trả về, rồi mới viết regex.

## Chạy tự động hằng ngày (GitHub Actions)

```yaml
# .github/workflows/nvl-prices.yml
on:
  schedule:
    - cron: "0 10 * * 1-5"   # 17:00 giờ Việt Nam, sau khi 100ppi/MPOC/LME đã công bố
  workflow_dispatch:
jobs:
  scrape:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r examples/raw-material-prices/requirements.txt
      - run: python scrape_prices.py --csv prices.csv
        working-directory: examples/raw-material-prices
        env:
          FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}
      - run: |
          git config user.name "nvl-bot" && git config user.email "nvl-bot@users.noreply.github.com"
          git add examples/raw-material-prices/prices.csv
          git commit -m "Cập nhật giá NVL $(date +%F)" || echo "Không có giá mới"
          git push
```

Có thể thay CSV bằng Google Sheets hoặc database: chỉ cần thay hàm `append_csv`.

## Lưu ý

- **LME**: giá được nạp bằng JavaScript và nằm ngoài vùng "main content". Nếu thiếu
  `wait_for` hoặc để `only_main_content=True` thì trang về rỗng. Trang công khai chỉ có
  giá day-delayed. Giá Cash/3M bid-offer chi tiết và lịch sử cần tài khoản LME.
- **100ppi**: giá trong ngày thường công bố trước 14h (giờ Trung Quốc). Trước giờ đó,
  dòng hôm nay là `-` và script lấy giá của ngày gần nhất.
- **Investing**: hợp đồng CPO trên trang này niêm yết bằng USD (CME), khác với giá MYR của Bursa trên MPOC.
- Hãy tuân thủ điều khoản sử dụng của từng trang. Investing.com và LME không cho phép
  phân phối lại dữ liệu của họ, nên chỉ dùng cho mục đích nội bộ.
