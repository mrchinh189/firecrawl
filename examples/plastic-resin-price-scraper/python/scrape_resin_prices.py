"""
Cao gia nguyen vat lieu nhua nguyen sinh PP / PE bang Firecrawl Cloud.

Cach dung:
    export FIRECRAWL_API_KEY=fc-...
    pip install -r requirements.txt
    python scrape_resin_prices.py

Ket qua ghi ra thu muc ../output/ duoi dang JSON + CSV.

Cau hinh nguon va schema o file ../sources.json (sua url / enabled / prompt tuy y).
"""

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from firecrawl import Firecrawl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONFIG_PATH = ROOT / "sources.json"
OUTPUT_DIR = ROOT / "output"

# Cac cot xuat ra CSV (theo schema trong sources.json)
CSV_FIELDS = [
    "source",
    "material",
    "grade",
    "price",
    "currency",
    "unit",
    "region",
    "date",
    "change",
    "scraped_at",
]


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"Khong tim thay file cau hinh: {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_client() -> Firecrawl:
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        sys.exit(
            "Thieu FIRECRAWL_API_KEY. Lay key tai https://firecrawl.dev roi:\n"
            "    export FIRECRAWL_API_KEY=fc-..."
        )
    return Firecrawl(api_key=api_key)


def scrape_source(client: Firecrawl, source: dict, schema: dict, scrape_cfg: dict) -> list[dict]:
    """Scrape mot nguon, tra ve danh sach dong gia da lam phang."""
    name = source["name"]
    url = source["url"]
    print(f"  -> [{name}] dang scrape: {url}")

    json_format = {"type": "json", "schema": schema}
    if source.get("prompt"):
        json_format["prompt"] = source["prompt"]

    try:
        doc = client.scrape(
            url,
            formats=[json_format],
            only_main_content=scrape_cfg.get("onlyMainContent", True),
            timeout=scrape_cfg.get("timeoutMs", 60000),
            max_age=scrape_cfg.get("maxAgeMs", 3600000),
        )
    except Exception as exc:  # noqa: BLE001 - bao loi tung nguon, khong dung ca chuong trinh
        print(f"     [LOI] {name}: {exc}")
        return []

    data = getattr(doc, "json", None) or {}
    prices = data.get("prices", []) if isinstance(data, dict) else []
    scraped_at = datetime.now(timezone.utc).isoformat()

    rows = []
    for p in prices:
        if not isinstance(p, dict):
            continue
        rows.append(
            {
                "source": name,
                "material": p.get("material") or source.get("material", ""),
                "grade": p.get("grade", ""),
                "price": p.get("price", ""),
                "currency": p.get("currency", ""),
                "unit": p.get("unit", ""),
                "region": p.get("region", ""),
                "date": p.get("date", ""),
                "change": p.get("change", ""),
                "scraped_at": scraped_at,
            }
        )
    print(f"     OK: {len(rows)} dong gia")
    return rows


def write_outputs(rows: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUTPUT_DIR / f"resin_prices_{stamp}.json"
    csv_path = OUTPUT_DIR / f"resin_prices_{stamp}.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDa ghi {len(rows)} dong gia vao:")
    print(f"  - {json_path}")
    print(f"  - {csv_path}")


def main() -> None:
    cfg = load_config()
    client = build_client()
    schema = cfg["schema"]
    scrape_cfg = cfg.get("scrape", {})
    sources = [s for s in cfg["sources"] if s.get("enabled", False)]

    if not sources:
        sys.exit("Khong co nguon nao duoc bat (enabled=true) trong sources.json")

    print(f"Bat dau cao gia tu {len(sources)} nguon...\n")
    all_rows: list[dict] = []
    for source in sources:
        all_rows.extend(scrape_source(client, source, schema, scrape_cfg))

    if not all_rows:
        print("\nKhong trich xuat duoc dong gia nao. Kiem tra lai URL / prompt / schema.")
        return

    write_outputs(all_rows)


if __name__ == "__main__":
    main()
