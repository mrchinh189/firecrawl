"""Backend API cho dashboard theo doi gia nhua PP/PE."""
import io
import os

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import db

API_TOKEN = os.environ.get("API_TOKEN", "")  # neu trong => mo, khong yeu cau token

app = FastAPI(title="Resin Price Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)


def require_token(x_api_token: str = Header(default="")):
    if API_TOKEN and x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Token khong hop le")
    return True


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/materials", dependencies=[Depends(require_token)])
def materials():
    rows = db.query("SELECT DISTINCT material FROM prices ORDER BY material")
    return [r["material"] for r in rows]


@app.get("/api/regions", dependencies=[Depends(require_token)])
def regions():
    rows = db.query(
        "SELECT DISTINCT region FROM prices WHERE region <> '' ORDER BY region"
    )
    return [r["region"] for r in rows]


@app.get("/api/sources", dependencies=[Depends(require_token)])
def sources():
    return db.query("SELECT name, url, material, enabled FROM sources ORDER BY name")


@app.get("/api/prices/latest", dependencies=[Depends(require_token)])
def latest(
    material: str | None = Query(default=None),
    region: str | None = Query(default=None),
):
    """Gia moi nhat cho moi (nguon, material, grade, region)."""
    sql = """
        SELECT DISTINCT ON (source_name, material, grade, region)
            source_name, material, grade, region,
            price_usd_ton, price_vnd_ton, fx_usd_vnd, price_date, scraped_at
        FROM prices
        WHERE (%(material)s IS NULL OR material = %(material)s)
          AND (%(region)s IS NULL OR region = %(region)s)
        ORDER BY source_name, material, grade, region,
                 price_date DESC NULLS LAST, scraped_at DESC
    """
    return db.query(sql, {"material": material, "region": region})


@app.get("/api/prices/history", dependencies=[Depends(require_token)])
def history(
    material: str = Query(...),
    region: str | None = Query(default=None),
    weeks: int = Query(default=26, ge=1, le=260),
):
    """Lich su gia trung binh theo ngay cua mot loai nhua (de ve bieu do xu huong)."""
    sql = """
        SELECT price_date,
               ROUND(AVG(price_usd_ton)) AS price_usd_ton,
               ROUND(AVG(price_vnd_ton)) AS price_vnd_ton
        FROM prices
        WHERE material = %(material)s
          AND price_date IS NOT NULL
          AND price_date >= CURRENT_DATE - (%(weeks)s * 7)
          AND (%(region)s IS NULL OR region = %(region)s)
        GROUP BY price_date
        ORDER BY price_date
    """
    return db.query(sql, {"material": material, "region": region, "weeks": weeks})


def _all_rows():
    return db.query(
        """SELECT source_name, material, grade, region, price_raw, currency_raw,
                  unit_raw, price_usd_ton, price_vnd_ton, fx_usd_vnd,
                  price_date, scraped_at
           FROM prices ORDER BY price_date DESC NULLS LAST, material"""
    )


@app.get("/api/export.csv", dependencies=[Depends(require_token)])
def export_csv():
    import csv

    rows = _all_rows()
    buf = io.StringIO()
    fields = list(rows[0].keys()) if rows else ["material", "price_usd_ton"]
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=resin_prices.csv"},
    )


@app.get("/api/export.xlsx", dependencies=[Depends(require_token)])
def export_xlsx():
    from openpyxl import Workbook

    rows = _all_rows()
    wb = Workbook()
    ws = wb.active
    ws.title = "Resin Prices"
    if rows:
        headers = list(rows[0].keys())
        ws.append(headers)
        for r in rows:
            ws.append([r[h] for h in headers])
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=resin_prices.xlsx"},
    )
