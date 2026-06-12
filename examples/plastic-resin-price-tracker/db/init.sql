-- Schema cho he thong theo doi gia nhua nguyen sinh PP/PE
-- Chay tu dong khi khoi tao container postgres (docker-entrypoint-initdb.d)

CREATE TABLE IF NOT EXISTS sources (
    id          SERIAL PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL,
    url         TEXT NOT NULL,
    material    TEXT,
    enabled     BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS prices (
    id              BIGSERIAL PRIMARY KEY,
    source_id       INT REFERENCES sources(id) ON DELETE SET NULL,
    source_name     TEXT NOT NULL,
    material        TEXT NOT NULL,          -- PP/PE/HDPE/LDPE/LLDPE/Other
    grade           TEXT NOT NULL DEFAULT '',
    region          TEXT NOT NULL DEFAULT '',
    price_raw       NUMERIC,                -- gia goc nhu cao duoc
    currency_raw    TEXT,                   -- USD/EUR/CNY...
    unit_raw        TEXT,                   -- USD/ton, USD/lb, USD/kg...
    price_usd_ton   NUMERIC,                -- gia chuan hoa ve USD/tan
    price_vnd_ton   NUMERIC,                -- gia quy doi ra VND/tan
    fx_usd_vnd      NUMERIC,                -- ti gia USD->VND tai thoi diem
    price_date      DATE,                   -- ngay/ky cua gia
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Dedup: 1 nguon + grade + region + ngay chi luu 1 ban ghi
    UNIQUE (source_name, material, grade, region, price_date)
);

CREATE INDEX IF NOT EXISTS idx_prices_material_date ON prices (material, price_date DESC);
CREATE INDEX IF NOT EXISTS idx_prices_scraped_at ON prices (scraped_at DESC);

CREATE TABLE IF NOT EXISTS collection_runs (
    id          BIGSERIAL PRIMARY KEY,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status      TEXT NOT NULL DEFAULT 'running',  -- running/success/partial/failed
    rows_added  INT NOT NULL DEFAULT 0,
    notes       TEXT
);
