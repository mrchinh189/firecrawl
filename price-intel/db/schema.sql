-- schema.sql — Supabase Postgres cho price-intel. Idempotent (chạy lại không vỡ DB).
-- Chạy: psql "$SUPABASE_DB_URL" -f db/schema.sql

-- Bảng nền: giá thô (staging) -> QC -> price_master (1 nguồn chân lý)
create table if not exists staging_prices(
  id bigserial primary key,
  date date, product text, grade text, region text, incoterm text,
  currency text, unit text, value numeric, price_type text,
  source text, note text, created_at timestamptz default now());

create table if not exists price_master(
  date date, product text, grade text, region text, incoterm text,
  currency text, unit text, value numeric, price_type text,
  value_vnd_kg numeric, source text, note text,
  created_at timestamptz default now(),
  primary key(date, product, region, source, price_type));

create table if not exists fx_rates(
  date date, pair text, rate numeric, source text,
  primary key(date, pair));

create table if not exists forecast(
  run_date date, product text, week int, yhat numeric, lower numeric,
  upper numeric, model text, mape numeric,
  created_at timestamptz default now(),
  primary key(run_date, product, week));

create table if not exists audit_log(
  id bigserial primary key, ts timestamptz default now(),
  table_name text, action text, detail text);

-- Phase 1: bảng & cột mới (idempotent)
alter table if exists staging_prices add column if not exists payment_term text default 'at_sight';
alter table if exists price_master  add column if not exists payment_term text default 'at_sight';
alter table if exists forecast add column if not exists theils_u numeric;
alter table if exists forecast add column if not exists confidence text;
alter table if exists forecast add column if not exists basis text;
create table if not exists spreads(
  date date, name text, value numeric, unit text, signal text, note text,
  created_at timestamptz default now());
create table if not exists landed(
  date date, product text, region text, price_type text, payment_term text,
  raw_price numeric, raw_unit text, usd_per_ton numeric, landed_vnd_kg numeric,
  usance_benefit numeric, at_sight_equiv numeric, is_best boolean, source text,
  created_at timestamptz default now());
create table if not exists news(
  id bigserial primary key, published_at date, title text, summary text,
  url text unique, source text, category text, created_at timestamptz default now());
create table if not exists analysis(
  run_date date, kind text, payload jsonb, created_at timestamptz default now(),
  primary key(run_date, kind));
