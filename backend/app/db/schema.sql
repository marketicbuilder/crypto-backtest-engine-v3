-- Supabase / PostgreSQL schema for the AI Crypto Backtest Engine.
-- Run inside the Supabase SQL editor or via `psql -f schema.sql`.

create extension if not exists "uuid-ossp";

-- ------------------------------------------------------------- users
-- Supabase already provisions auth.users; we keep a public mirror so we
-- can attach foreign keys without touching the auth schema.
create table if not exists public.users (
  id            uuid primary key default uuid_generate_v4(),
  auth_id       uuid unique,
  email         text unique,
  display_name  text,
  created_at    timestamptz not null default now()
);

-- -------------------------------------------------------- strategies
create table if not exists public.strategies (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid references public.users(id) on delete cascade,
  name          text not null,
  base          text not null,         -- which plug-in (e.g. "ai_scoring")
  params        jsonb not null default '{}'::jsonb,
  description   text,
  is_template   boolean not null default false,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index if not exists strategies_user_idx on public.strategies(user_id);

-- --------------------------------------------------------- datasets
-- Cached historical-price downloads so backtests can be re-run for free.
create table if not exists public.datasets (
  id            uuid primary key default uuid_generate_v4(),
  symbol        text not null,
  source        text not null,
  interval      text not null,
  start_ts      timestamptz not null,
  end_ts        timestamptz not null,
  bars          integer not null,
  storage_path  text,                  -- supabase storage object key
  created_at    timestamptz not null default now(),
  unique (symbol, source, interval, start_ts, end_ts)
);

-- -------------------------------------------------------- backtests
create table if not exists public.backtests (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid references public.users(id) on delete cascade,
  strategy_id   uuid references public.strategies(id) on delete set null,
  dataset_id    uuid references public.datasets(id) on delete set null,
  config        jsonb not null,        -- BacktestConfig + DataRequest
  metrics       jsonb not null,        -- full metrics dict
  insights      jsonb,
  created_at    timestamptz not null default now()
);
create index if not exists backtests_user_idx     on public.backtests(user_id);
create index if not exists backtests_strategy_idx on public.backtests(strategy_id);

-- ----------------------------------------------------------- trades
create table if not exists public.trades (
  id            uuid primary key default uuid_generate_v4(),
  backtest_id   uuid references public.backtests(id) on delete cascade,
  entry_time    timestamptz not null,
  exit_time     timestamptz not null,
  side          text not null check (side in ('long','short')),
  entry_price   double precision not null,
  exit_price    double precision not null,
  qty           double precision not null,
  pnl           double precision not null,
  pnl_pct       double precision not null,
  fees          double precision not null default 0,
  score         double precision not null default 0,
  reason_entry  text,
  reason_exit   text
);
create index if not exists trades_backtest_idx on public.trades(backtest_id);
create index if not exists trades_time_idx     on public.trades(entry_time);

-- -------------------------------------------------- optimisation runs
create table if not exists public.optimisations (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid references public.users(id) on delete cascade,
  strategy_base text not null,
  param_grid    jsonb not null,
  objective     text not null,
  best_params   jsonb,
  best_metrics  jsonb,
  table_rows    jsonb,                 -- compact ranking table
  created_at    timestamptz not null default now()
);

-- ----------------------------------------------------- row-level security
alter table public.strategies   enable row level security;
alter table public.backtests    enable row level security;
alter table public.trades       enable row level security;
alter table public.optimisations enable row level security;

create policy "owner reads strategies"
  on public.strategies for select
  using (user_id is null or user_id = auth.uid());

create policy "owner writes strategies"
  on public.strategies for all
  using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "owner reads backtests"
  on public.backtests for select using (user_id = auth.uid());
create policy "owner writes backtests"
  on public.backtests for all using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "trades follow backtest owner"
  on public.trades for select using (
    exists (select 1 from public.backtests b where b.id = trades.backtest_id and b.user_id = auth.uid())
  );
