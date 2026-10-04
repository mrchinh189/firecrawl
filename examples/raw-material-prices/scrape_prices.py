"""
Cào giá nguyên vật liệu (NVL) bằng Firecrawl.

Mỗi nguồn được khai báo trong SOURCES gồm: URL, tuỳ chọn scrape riêng cho trang đó,
và một hàm parse chuyển markdown của Firecrawl thành một bản ghi giá.
Nếu parser không đọc được (trang đổi giao diện), script tự chuyển sang
chế độ trích xuất JSON bằng LLM của Firecrawl (formats=["json"]).

Chạy:
    export FIRECRAWL_API_KEY=fc-...
    python scrape_prices.py                 # in kết quả + ghi vào prices.csv
    python scrape_prices.py --only lme_zinc # chỉ chạy một nguồn
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class PriceRecord:
    source: str
    material: str
    price: float
    unit: str
    price_date: Optional[str] = None  # YYYY-MM-DD, ngày của giá (không phải ngày cào)
    change_pct: Optional[float] = None
    url: str = ""
    method: str = "parser"  # "parser" | "llm"
    scraped_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


def to_number(text: str) -> float:
    return float(text.replace(",", "").strip())


# --------------------------------------------------------------------------- #
# Parsers: nhận markdown (+ metadata) do Firecrawl trả về, trả dict các trường giá.
# Hàm thuần, không gọi mạng -> test được offline (xem test_parsers.py).
# --------------------------------------------------------------------------- #

def parse_investing(markdown: str, metadata: Dict[str, Any], today: date) -> Dict[str, Any]:
    """vn.investing.com: giá cuối, % thay đổi và ngày 'Đóng cửa·dd/mm'."""
    m = re.search(
        r"^\s*([\d,]+\.\d+)\s*\n+\s*([+-][\d,.]+)\(([+-][\d.]+)%\)",
        markdown,
        re.MULTILINE,
    )
    if m:
        price, change_pct = to_number(m.group(1)), float(m.group(3))
    else:
        # Fallback: Investing nhúng giá trong thẻ meta "global-translation-variables".
        raw = metadata.get("global-translation-variables")
        variables = json.loads(json.loads(raw)) if raw else {}
        if not variables.get("LAST_PRICE"):
            raise ValueError("investing: không tìm thấy giá")
        price, change_pct = to_number(variables["LAST_PRICE"]), None

    price_date = None
    d = re.search(r"·\s*(\d{2})/(\d{2})", markdown)
    if d:
        price_date = _infer_year(int(d.group(2)), int(d.group(1)), today)
    return {"price": price, "change_pct": change_pct, "price_date": price_date}


def parse_100ppi(markdown: str, metadata: Dict[str, Any], today: date) -> Dict[str, Any]:
    """100ppi (生意社): bảng | 日期 | 价格 | 日涨跌 |, lấy dòng mới nhất có giá."""
    for m in re.finditer(r"^\|\s*(\d{2})-(\d{2})\s*\|\s*([\d,.]+|-)\s*\|\s*([+-]?[\d.]+|-)%\s*\|", markdown, re.MULTILINE):
        month, day, price, pct = m.groups()
        if price == "-":
            continue  # ngày hiện tại thường chưa có giá (công bố trước 14h)
        return {
            "price": to_number(price),
            "change_pct": None if pct == "-" else float(pct),
            "price_date": _infer_year(int(month), int(day), today),
        }
    raise ValueError("100ppi: không tìm thấy dòng giá")


def parse_mpoc(markdown: str, metadata: Dict[str, Any], today: date) -> Dict[str, Any]:
    """MPOC: bảng 'CPO Prices' (Settlement Price RM), dòng cuối là mới nhất."""
    section = markdown.split("## CPO Prices", 1)[-1]
    rows = re.findall(r"^\|\s*(\d{1,2} [A-Za-z]{3} \d{2})\s*\|\s*([\d,.]+)\s*\|", section, re.MULTILINE)
    if not rows:
        raise ValueError("mpoc: không tìm thấy bảng CPO Prices")
    parsed = [(datetime.strptime(d, "%d %b %y").date(), to_number(p)) for d, p in rows]
    parsed.sort()
    (last_date, last_price) = parsed[-1]
    change_pct = None
    if len(parsed) > 1 and parsed[-2][1]:
        change_pct = round((last_price / parsed[-2][1] - 1) * 100, 2)
    return {"price": last_price, "change_pct": change_pct, "price_date": last_date.isoformat()}


def parse_lme(markdown: str, metadata: Dict[str, Any], today: date) -> Dict[str, Any]:
    """LME: '3-month Closing Price (day-delayed)' ở khối đầu trang (render bằng JS)."""
    m = re.search(r"([\d,]+\.\d+)\s*\n+\s*([+-]?[\d.]+)%\s*\n+\s*3-month Closing Price", markdown)
    if not m:
        raise ValueError("lme: không tìm thấy 3-month Closing Price")
    price_date = None
    d = re.search(r"Data valid for (\d{1,2} [A-Za-z]{3} \d{4})", markdown)
    if d:
        price_date = datetime.strptime(d.group(1), "%d %b %Y").date().isoformat()
    return {"price": to_number(m.group(1)), "change_pct": float(m.group(2)), "price_date": price_date}


def _infer_year(month: int, day: int, today: date) -> str:
    """Trang chỉ ghi dd/mm: nếu tháng lớn hơn tháng hiện tại thì là năm trước."""
    year = today.year - 1 if month > today.month else today.year
    return date(year, month, day).isoformat()


# --------------------------------------------------------------------------- #
# Cấu hình nguồn. Thêm NVL mới = thêm một phần tử vào đây.
# --------------------------------------------------------------------------- #

@dataclass
class Source:
    key: str
    material: str
    url: str
    unit: str
    parser: Callable[[str, Dict[str, Any], date], Dict[str, Any]]
    scrape_options: Dict[str, Any] = field(default_factory=dict)


SOURCES: List[Source] = [
    Source(
        key="investing_cpo",
        material="Dầu cọ thô Malaysia (CPO futures, CPOc1)",
        url="https://vn.investing.com/commodities/malaysian-crude-palm-oil-futures-streaming-chart",
        unit="USD/tấn",
        parser=parse_investing,
        scrape_options={"only_main_content": True},
    ),
    Source(
        key="100ppi_sulfuric_acid",
        material="Axit sunfuric (硫酸) - giá cơ sở 生意社",
        url="https://m1.100ppi.com/vane/236-%E7%A1%AB%E9%85%B8.html",
        unit="CNY/tấn",
        parser=parse_100ppi,
        scrape_options={"only_main_content": True},
    ),
    Source(
        key="mpoc_cpo",
        material="Dầu cọ thô (CPO) - giá thanh toán Bursa Malaysia",
        url="https://www.mpoc.org.my/market-insight/daily-palm-oil-prices/",
        unit="MYR/tấn",
        parser=parse_mpoc,
        scrape_options={"only_main_content": True},
    ),
    Source(
        key="lme_zinc",
        material="Kẽm LME (3-month closing, day-delayed)",
        url="https://www.lme.com/en/Metals/Non-ferrous/LME-Zinc",
        unit="USD/tấn",
        parser=parse_lme,
        # Giá được render bằng JS và nằm ngoài "main content" -> phải chờ và lấy toàn trang.
        scrape_options={"only_main_content": False, "wait_for": 12000},
    ),
]

LLM_SCHEMA = {
    "type": "object",
    "properties": {
        "price": {"type": "number", "description": "Giá mới nhất của hàng hoá chính trên trang"},
        "change_pct": {"type": "number", "description": "% thay đổi so với phiên trước"},
        "price_date": {"type": "string", "description": "Ngày của giá, định dạng YYYY-MM-DD"},
    },
    "required": ["price"],
}


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #

def _metadata_dict(doc: Any) -> Dict[str, Any]:
    md = getattr(doc, "metadata", None)
    if md is None:
        return {}
    return md.model_dump() if hasattr(md, "model_dump") else dict(md)


def scrape_source(app: Any, source: Source, use_llm_fallback: bool = True) -> PriceRecord:
    # max_age=0: luôn lấy bản mới, không dùng cache của Firecrawl (giá thay đổi hằng ngày).
    doc = app.scrape(source.url, formats=["markdown"], max_age=0, **source.scrape_options)
    try:
        fields = source.parser(doc.markdown or "", _metadata_dict(doc), date.today())
        method = "parser"
    except Exception as parse_error:
        if not use_llm_fallback:
            raise
        print(f"[{source.key}] parser lỗi ({parse_error}), chuyển sang trích xuất LLM", file=sys.stderr)
        doc = app.scrape(
            source.url,
            formats=[{
                "type": "json",
                "schema": LLM_SCHEMA,
                "prompt": f"Lấy giá mới nhất của: {source.material}. Đơn vị: {source.unit}.",
            }],
            max_age=0,
            **source.scrape_options,
        )
        fields = doc.json or {}
        if not fields.get("price"):
            raise ValueError(f"{source.key}: LLM cũng không trích xuất được giá") from parse_error
        method = "llm"

    return PriceRecord(
        source=source.key,
        material=source.material,
        unit=source.unit,
        url=source.url,
        method=method,
        price=float(fields["price"]),
        change_pct=fields.get("change_pct"),
        price_date=fields.get("price_date"),
    )


def append_csv(path: Path, records: List[PriceRecord]) -> int:
    """Ghi nối vào CSV lịch sử, bỏ qua bản ghi trùng (source, price_date, price)."""
    columns = list(PriceRecord.__dataclass_fields__.keys())
    seen = set()
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                seen.add((row["source"], row["price_date"], float(row["price"])))
    new = [r for r in records if (r.source, r.price_date or "", r.price) not in seen]
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if write_header:
            writer.writeheader()
        for r in new:
            writer.writerow(asdict(r))
    return len(new)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cào giá NVL bằng Firecrawl")
    parser.add_argument("--only", nargs="*", help="Chỉ chạy các source key này")
    parser.add_argument("--csv", default="prices.csv", help="File CSV lưu lịch sử giá")
    parser.add_argument("--no-llm", action="store_true", help="Tắt fallback trích xuất bằng LLM")
    args = parser.parse_args()

    from firecrawl import Firecrawl  # pip install firecrawl-py

    app = Firecrawl(
        api_key=os.environ.get("FIRECRAWL_API_KEY"),
        api_url=os.environ.get("FIRECRAWL_API_URL", "https://api.firecrawl.dev"),
    )

    sources = [s for s in SOURCES if not args.only or s.key in args.only]
    records, failed = [], []
    for source in sources:
        try:
            record = scrape_source(app, source, use_llm_fallback=not args.no_llm)
            records.append(record)
            change = f"{record.change_pct:+.2f}%" if record.change_pct is not None else "n/a"
            print(f"{record.material:<50} {record.price:>12,.2f} {record.unit:<8} {change:>8}  ({record.price_date})")
        except Exception as e:  # một nguồn lỗi không làm hỏng cả lượt chạy
            failed.append(source.key)
            print(f"[{source.key}] LỖI: {e}", file=sys.stderr)

    added = append_csv(Path(args.csv), records)
    print(f"\nĐã ghi {added} bản ghi mới vào {args.csv}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
