'use client';
import { Suspense, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Card, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input, Label } from '@/components/ui/input';
import { KpiCard, MetricsTable } from '@/components/MetricsTable';
import { TradeTable, exportCSV } from '@/components/TradeTable';
import { DrawdownChart, EquityCurve } from '@/components/charts/EquityCurve';
import { api, type BacktestRequest, type BacktestResponse, type Strategy } from '@/lib/api';
import { fmt } from '@/lib/utils';

function Page() {
  const params = useSearchParams();
  const initialStrategy = params.get('strategy') || 'ai_scoring';

  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [form, setForm] = useState({
    symbol: 'BTCUSDT', interval: '1D', source: 'bitget',
    start: '', end: '', starting_balance: 10000,
    fee_pct: 0.001, slippage_pct: 0.0005,
    risk_per_trade: 0.02, stop_loss_pct: 0.08, take_profit_pct: 0.25,
    trailing_stop_pct: 0.10, leverage: 1, allow_short: false,
    strategy: initialStrategy,
  });
  const [paramOverrides, setParamOverrides] = useState<Record<string, number>>({});
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { api.strategies().then(setStrategies); }, []);

  const currentStrategy = useMemo(
    () => strategies.find(s => s.name === form.strategy),
    [strategies, form.strategy],
  );

  async function run() {
    setLoading(true); setError(null);
    try {
      const req: BacktestRequest = {
        data: {
          symbol: form.symbol, interval: form.interval, source: form.source,
          start: form.start || undefined, end: form.end || undefined,
          with_fear_greed: true,
        },
        strategy: { name: form.strategy, params: paramOverrides },
        starting_balance: +form.starting_balance,
        fee_pct: +form.fee_pct, slippage_pct: +form.slippage_pct,
        risk_per_trade: +form.risk_per_trade,
        stop_loss_pct: +form.stop_loss_pct, take_profit_pct: +form.take_profit_pct,
        trailing_stop_pct: +form.trailing_stop_pct, leverage: +form.leverage,
        allow_short: form.allow_short,
      };
      const res = await api.runBacktest(req);
      setResult(res);
      try {
        const prev = JSON.parse(localStorage.getItem('recent_backtests') || '[]');
        prev.unshift({ ts: Date.now(), symbol: form.symbol, strategy: res.strategy, metrics: res.metrics });
        localStorage.setItem('recent_backtests', JSON.stringify(prev.slice(0, 20)));
      } catch {}
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  function downloadCSV() {
    if (!result) return;
    const blob = new Blob([exportCSV(result.trades)], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `trades_${form.symbol}_${form.strategy}.csv`; a.click();
    URL.revokeObjectURL(url);
  }

  function downloadJSON() {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `backtest_${form.symbol}_${form.strategy}.json`; a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold">Run a backtest</h1>
        <p className="text-slate-400 mt-1">Configure the dataset, strategy parameters and trade rules.</p>
      </header>

      <Card>
        <CardHeader title="Configuration" />
        <div className="grid md:grid-cols-4 gap-4">
          <div><Label>Strategy</Label>
            <select className="w-full rounded-md border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm"
              value={form.strategy} onChange={e => { setForm({ ...form, strategy: e.target.value }); setParamOverrides({}); }}>
              {strategies.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
            </select>
          </div>
          <div><Label>Symbol</Label><Input value={form.symbol} onChange={e => setForm({ ...form, symbol: e.target.value.toUpperCase() })} /></div>
          <div><Label>Interval</Label>
            <select className="w-full rounded-md border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm"
              value={form.interval} onChange={e => setForm({ ...form, interval: e.target.value })}>
              {['1H', '4H', '1D', '1W'].map(i => <option key={i}>{i}</option>)}
            </select>
          </div>
          <div><Label>Source</Label>
            <select className="w-full rounded-md border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm"
              value={form.source} onChange={e => setForm({ ...form, source: e.target.value })}>
              <option value="bitget">bitget</option>
            </select>
          </div>
          <div><Label>Start (YYYY-MM-DD)</Label><Input placeholder="2021-01-01" value={form.start} onChange={e => setForm({ ...form, start: e.target.value })} /></div>
          <div><Label>End</Label><Input placeholder="2026-01-01" value={form.end} onChange={e => setForm({ ...form, end: e.target.value })} /></div>
          <div><Label>Starting balance ($)</Label><Input type="number" value={form.starting_balance} onChange={e => setForm({ ...form, starting_balance: +e.target.value })} /></div>
          <div><Label>Leverage</Label><Input type="number" value={form.leverage} step="0.5" onChange={e => setForm({ ...form, leverage: +e.target.value })} /></div>
          <div><Label>Fee %</Label><Input type="number" step="0.0001" value={form.fee_pct} onChange={e => setForm({ ...form, fee_pct: +e.target.value })} /></div>
          <div><Label>Slippage %</Label><Input type="number" step="0.0001" value={form.slippage_pct} onChange={e => setForm({ ...form, slippage_pct: +e.target.value })} /></div>
          <div><Label>Risk / trade</Label><Input type="number" step="0.005" value={form.risk_per_trade} onChange={e => setForm({ ...form, risk_per_trade: +e.target.value })} /></div>
          <div><Label>Stop-loss %</Label><Input type="number" step="0.005" value={form.stop_loss_pct} onChange={e => setForm({ ...form, stop_loss_pct: +e.target.value })} /></div>
          <div><Label>Take-profit %</Label><Input type="number" step="0.01" value={form.take_profit_pct} onChange={e => setForm({ ...form, take_profit_pct: +e.target.value })} /></div>
          <div><Label>Trailing stop %</Label><Input type="number" step="0.01" value={form.trailing_stop_pct} onChange={e => setForm({ ...form, trailing_stop_pct: +e.target.value })} /></div>
          <div className="flex items-end"><label className="inline-flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.allow_short} onChange={e => setForm({ ...form, allow_short: e.target.checked })} />
            Allow shorting
          </label></div>
        </div>

        {currentStrategy && Object.keys(currentStrategy.params).length > 0 && (
          <div className="mt-6">
            <CardHeader title="Strategy parameters" subtitle={`Overrides for ${currentStrategy.name}`} />
            <div className="grid md:grid-cols-4 gap-4">
              {Object.entries(currentStrategy.params).map(([k, v]) => (
                <div key={k}>
                  <Label>{k}</Label>
                  <Input type="number" defaultValue={v}
                    onChange={e => setParamOverrides({ ...paramOverrides, [k]: +e.target.value })} />
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-3 mt-6">
          <Button onClick={run} disabled={loading}>{loading ? 'Running…' : 'Run backtest'}</Button>
          {result && <>
            <Button variant="secondary" onClick={downloadCSV}>Export CSV</Button>
            <Button variant="secondary" onClick={downloadJSON}>Export JSON</Button>
          </>}
        </div>
        {error && <div className="mt-3 text-sm text-rose-400">{error}</div>}
      </Card>

      {result && <>
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard label="Total return" value={fmt.pct(result.metrics.total_return)} good={result.metrics.total_return >= 0} />
          <KpiCard label="Sharpe" value={fmt.num(result.metrics.sharpe_ratio)} good={result.metrics.sharpe_ratio >= 1} />
          <KpiCard label="Max DD" value={fmt.pct(result.metrics.max_drawdown)} good={result.metrics.max_drawdown > -0.2} />
          <KpiCard label="Win rate" value={fmt.pct(result.metrics.win_rate, 1)} good={result.metrics.win_rate >= 0.5} />
          <KpiCard label="Profit factor" value={fmt.num(result.metrics.profit_factor)} good={result.metrics.profit_factor >= 1.5} />
          <KpiCard label="Trades" value={String(result.metrics.total_trades)} />
          <KpiCard label="Avg win" value={fmt.money(result.metrics.average_win, 2)} good />
          <KpiCard label="Avg loss" value={fmt.money(result.metrics.average_loss, 2)} good={false} />
        </section>

        <section className="grid lg:grid-cols-2 gap-6">
          <Card><CardHeader title="Equity curve" /><EquityCurve data={result.equity} /></Card>
          <Card><CardHeader title="Drawdown" /><DrawdownChart data={result.drawdown} /></Card>
        </section>

        <section>
          <CardHeader title="Key metrics" subtitle="" />
          <MetricsTable m={result.metrics} starting={+form.starting_balance} />
        </section>

        <section>
          <CardHeader title="AI insights" />
          <ul className="space-y-2">
            {result.insights.map((t, i) => (
              <li key={i} className="rounded-lg border border-slate-800 bg-slate-900/30 p-3 text-sm">
                <span className="text-sky-400 mr-2">▸</span>
                <span dangerouslySetInnerHTML={{ __html: t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') }} />
              </li>
            ))}
          </ul>
        </section>

        <section>
          <CardHeader title="Trade log" subtitle={`${result.trades.length} simulated trades`} />
          <TradeTable trades={result.trades} />
        </section>
      </>}
    </div>
  );
}

export default function BacktestsPage() {
  return <Suspense><Page /></Suspense>;
}
