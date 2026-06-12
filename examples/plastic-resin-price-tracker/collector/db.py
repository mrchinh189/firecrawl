"""Lop truy cap DB Postgres cho collector."""
import datetime as dt
import logging
from contextlib import contextmanager

import psycopg

import config

log = logging.getLogger("db")


@contextmanager
def get_conn():
    conn = psycopg.connect(config.DATABASE_URL, autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


def sync_sources(sources: list[dict]) -> None:
    """Upsert danh sach nguon tu sources.json vao bang sources."""
    with get_conn() as conn:
        for s in sources:
            conn.execute(
                """
                INSERT INTO sources (name, url, material, enabled)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE
                  SET url = EXCLUDED.url,
                      material = EXCLUDED.material,
                      enabled = EXCLUDED.enabled
                """,
                (s["name"], s["url"], s.get("material"), s.get("enabled", True)),
            )


def start_run() -> int:
    with get_conn() as conn:
        row = conn.execute(
            "INSERT INTO collection_runs (status) VALUES ('running') RETURNING id"
        ).fetchone()
        return row[0]


def finish_run(run_id: int, status: str, rows_added: int, notes: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            """UPDATE collection_runs
               SET finished_at = now(), status = %s, rows_added = %s, notes = %s
               WHERE id = %s""",
            (status, rows_added, notes[:2000], run_id),
        )


def get_previous_price(source_name: str, material: str, grade: str, region: str):
    """Lay gia USD/tan gan nhat truoc do (de so sanh canh bao)."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT price_usd_ton, price_date FROM prices
               WHERE source_name=%s AND material=%s AND grade=%s AND region=%s
               ORDER BY price_date DESC NULLS LAST, scraped_at DESC
               LIMIT 1""",
            (source_name, material, grade, region),
        ).fetchone()
        return row  # (price_usd_ton, price_date) hoac None


def upsert_price(source_name: str, row: dict) -> bool:
    """Ghi 1 ban ghi gia. Tra ve True neu them moi (khong trung)."""
    price_date = row.get("price_date") or dt.date.today().isoformat()
    with get_conn() as conn:
        result = conn.execute(
            """
            INSERT INTO prices
              (source_name, material, grade, region, price_raw, currency_raw,
               unit_raw, price_usd_ton, price_vnd_ton, fx_usd_vnd, price_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (source_name, material, grade, region, price_date)
            DO UPDATE SET
              price_raw=EXCLUDED.price_raw,
              price_usd_ton=EXCLUDED.price_usd_ton,
              price_vnd_ton=EXCLUDED.price_vnd_ton,
              fx_usd_vnd=EXCLUDED.fx_usd_vnd,
              scraped_at=now()
            RETURNING (xmax = 0) AS inserted
            """,
            (
                source_name, row["material"], row["grade"], row["region"],
                row["price_raw"], row["currency_raw"], row["unit_raw"],
                row["price_usd_ton"], row["price_vnd_ton"], row["fx_usd_vnd"],
                price_date,
            ),
        ).fetchone()
        return bool(result[0]) if result else False
