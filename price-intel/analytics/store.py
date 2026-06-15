# -*- coding: utf-8 -*-
"""store.py — đọc nguồn dữ liệu (DB nếu có, không thì fixtures CSV) + ghi kết quả.
Khi không có DB: ghi dry-run (in) — đủ để demo/test offline."""
import csv
import json
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent / "collect"))

FIX = pathlib.Path(__file__).resolve().parent.parent / "fixtures"


def _conn():
    try:
        from common import db   # collect/common.py
        return db()
    except Exception:
        return None


def read_price_master():
    """Trả list[dict]. Ưu tiên DB; fallback fixtures/price_master.csv."""
    conn = _conn()
    if conn is not None:
        import pandas as pd
        df = pd.read_sql("select * from price_master order by date", conn)
        conn.close()
        if not df.empty:
            return df.to_dict("records")
    with open(FIX / "price_master.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["value"] = float(r["value"])
    return rows


def read_latest_fx():
    conn = _conn()
    if conn is not None:
        cur = conn.cursor()
        cur.execute("select rate from fx_rates where pair='USD/VND' order by date desc limit 1")
        row = cur.fetchone(); conn.close()
        if row:
            return float(row[0])
    with open(FIX / "fx_rates.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return float(rows[-1]["rate"])


def read_news(limit=12):
    """Trả list[dict] tin tức. Ưu tiên DB (bảng news); fallback fixtures/news.csv."""
    conn = _conn()
    if conn is not None:
        import pandas as pd
        df = pd.read_sql("select published_at,title,url,summary,source,category "
                         "from news order by published_at desc limit %s", conn, params=(limit,))
        conn.close()
        if not df.empty:
            df["published_at"] = df["published_at"].astype(str)
            return df.to_dict("records")
    with open(FIX / "news.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit]


def write_rows(table, rows):
    """Ghi list[dict] vào bảng (DB) hoặc in dry-run."""
    conn = _conn()
    if conn is None or not rows:
        print(f"  (dry) {table}: {len(rows)} dòng")
        return len(rows)
    cols = list(rows[0].keys())
    ph = ",".join(f"%({c})s" for c in cols)
    q = f"insert into {table}({','.join(cols)}) values ({ph})"
    with conn, conn.cursor() as c:
        for r in rows:
            c.execute(q, r)
    conn.close(); print(f"[OK] {table} +{len(rows)} dòng")
    return len(rows)


def write_analysis(run_date, kind, payload):
    conn = _conn()
    if conn is None:
        print(f"  (dry) analysis[{kind}]: {json.dumps(payload, ensure_ascii=False)[:120]}")
        return
    with conn, conn.cursor() as c:
        c.execute("""insert into analysis(run_date,kind,payload) values(%s,%s,%s)
                     on conflict(run_date,kind) do update set payload=excluded.payload""",
                  (run_date, kind, json.dumps(payload, ensure_ascii=False)))
    conn.close(); print(f"[OK] analysis[{kind}]")
