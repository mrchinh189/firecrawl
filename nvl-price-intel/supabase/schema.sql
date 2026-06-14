-- Schema Supabase cho NVL Price Intel.
-- Chạy trong SQL Editor của Supabase (hoặc psql) trước khi đặt STORAGE_BACKEND=supabase.

create table if not exists public.prices (
    ticker  text    not null,
    date    text    not null,
    open    double precision,
    high    double precision,
    low     double precision,
    close   double precision,
    volume  bigint,
    primary key (ticker, date)
);

create table if not exists public.runs (
    id           bigint generated always as identity primary key,
    ticker       text not null,
    generated_at text not null,
    last_close   double precision,
    change_pct   double precision,
    summary      text,
    docx_path    text,
    ai_used      boolean
);

create index if not exists idx_prices_ticker on public.prices (ticker, date desc);
create index if not exists idx_runs_ticker on public.runs (ticker, generated_at desc);
