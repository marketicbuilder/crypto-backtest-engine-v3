'use client';
import { useEffect, useState } from 'react';
import { Card, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { KpiCard } from '@/components/MetricsTable';
import { api, type Strategy } from '@/lib/api';
import { fmt } from '@/lib/utils';
import Link from 'next/link';

export default function DashboardPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [recent, setRecent] = useState<any[]>([]);
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    api.health().then(() => setOk(true)).catch(() => setOk(false));
    api.strategies().then(setStrategies).catch(() => {});
    try {
      const raw = localStorage.getItem('recent_backtests');
      setRecent(raw ? JSON.parse(raw) : []);
    } catch {}
  }, []);

  const lastMetrics = recent[0]?.metrics ?? {};

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-widest text-sky-400/80">
            {ok == null ? 'connecting…' : ok ? 'backend online' : 'backend unreachable'}
          </div>
          <h1 className="text-3xl font-semibold mt-2">Dashboard</h1>
          <p className="text-slate-400 mt-1">Backtest AI trading strategies on 5y of crypto OHLCV.</p>
        </div>
        <Link href="/backtests"><Button>+ New backtest</Button></Link>
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Portfolio value" value={fmt.money(lastMetrics.final_balance ?? 10000)} good={!!lastMetrics.total_return && lastMetrics.total_return > 0} />
        <KpiCard label="Total return" value={fmt.pct(lastMetrics.total_return ?? 0)} good={(lastMetrics.total_return ?? 0) > 0} />
        <KpiCard label="Sharpe ratio" value={fmt.num(lastMetrics.sharpe_ratio ?? 0)} good={(lastMetrics.sharpe_ratio ?? 0) >= 1} />
        <KpiCard label="Max drawdown" value={fmt.pct(lastMetrics.max_drawdown ?? 0)} good={(lastMetrics.max_drawdown ?? 0) > -0.2} />
        <KpiCard label="Win rate" value={fmt.pct(lastMetrics.win_rate ?? 0, 1)} good={(lastMetrics.win_rate ?? 0) >= 0.5} />
        <KpiCard label="Profit factor" value={fmt.num(lastMetrics.profit_factor ?? 0)} good={(lastMetrics.profit_factor ?? 0) >= 1.5} />
        <KpiCard label="Trades" value={String(lastMetrics.total_trades ?? 0)} />
        <KpiCard label="Strategies" value={String(strategies.length)} />
      </section>

      <section className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Available strategies" subtitle="Plug-in registry" />
          <ul className="divide-y divide-slate-800">
            {strategies.map(s => (
              <li key={s.name} className="py-3 flex items-baseline justify-between">
                <div>
                  <div className="font-medium text-slate-100">{s.name}</div>
                  <div className="text-xs text-slate-500">
                    {Object.entries(s.params).slice(0, 4).map(([k, v]) => `${k}=${v}`).join(' · ')}
                  </div>
                </div>
                <Link href={`/backtests?strategy=${s.name}`}>
                  <Button variant="ghost" size="sm">Backtest →</Button>
                </Link>
              </li>
            ))}
            {strategies.length === 0 && <li className="text-slate-500 text-sm py-3">No strategies loaded.</li>}
          </ul>
        </Card>

        <Card>
          <CardHeader title="Recent backtests" subtitle="Stored in this browser" />
          <ul className="divide-y divide-slate-800">
            {recent.slice(0, 8).map((r, i) => (
              <li key={i} className="py-3 flex items-baseline justify-between text-sm">
                <div>
                  <div className="text-slate-200">{r.strategy?.name} · {r.symbol}</div>
                  <div className="text-xs text-slate-500">{new Date(r.ts).toLocaleString()}</div>
                </div>
                <div className={(r.metrics?.total_return ?? 0) >= 0 ? 'text-emerald-300' : 'text-rose-300'}>
                  {fmt.pct(r.metrics?.total_return ?? 0)}
                </div>
              </li>
            ))}
            {recent.length === 0 && <li className="text-slate-500 text-sm py-3">Run your first backtest →</li>}
          </ul>
        </Card>
      </section>
    </div>
  );
}
