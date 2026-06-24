/** API client for the FastAPI backend. */
const BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${await r.text()}`);
  return r.json() as Promise<T>;
}

export type Strategy = { name: string; params: Record<string, number> };
export type Trade = {
  entry_time: string; exit_time: string; side: 'long' | 'short';
  entry_price: number; exit_price: number; qty: number;
  pnl: number; pnl_pct: number; fees: number; score: number;
  reason_entry: string; reason_exit: string;
};
export type BacktestResponse = {
  metrics: Record<string, number>;
  trades: Trade[];
  equity: { t: string; v: number }[];
  drawdown: { t: string; v: number }[];
  insights: string[];
  strategy: Strategy;
};
export type BacktestRequest = {
  data: { symbol: string; interval: string; start?: string; end?: string;
          source?: string; with_fear_greed?: boolean; with_news?: boolean };
  strategy: Strategy;
  starting_balance?: number;
  fee_pct?: number; slippage_pct?: number;
  risk_per_trade?: number; max_open_positions?: number;
  stop_loss_pct?: number; take_profit_pct?: number;
  trailing_stop_pct?: number; leverage?: number; allow_short?: boolean;
};

export const api = {
  strategies: () => http<Strategy[]>('/strategies'),
  runBacktest: (req: BacktestRequest) =>
    http<BacktestResponse>('/backtests/run', { method: 'POST', body: JSON.stringify(req) }),
  compare: (req: { data: BacktestRequest['data']; strategies: Strategy[]; starting_balance?: number }) =>
    http<any[]>('/backtests/compare', { method: 'POST', body: JSON.stringify(req) }),
  optimise: (req: {
    data: BacktestRequest['data']; strategy_name: string;
    param_grid: Record<string, number[]>; objective?: string;
  }) =>
    http<{ best_params: Record<string, number>; best_metrics: Record<string, number>; table: any[] }>(
      '/backtests/optimise', { method: 'POST', body: JSON.stringify(req) }),
  ohlcv: (symbol: string, interval = '1d') =>
    http<{ t: string; o: number; h: number; l: number; c: number; v: number }[]>(
      `/data/ohlcv?symbol=${symbol}&interval=${interval}`),
  health: () => http<{ status: string }>('/health'),
};
