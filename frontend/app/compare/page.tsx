'use client';
import { useEffect, useState } from 'react';
import { Card, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input, Label } from '@/components/ui/input';
import { api, type Strategy } from '@/lib/api';
import { fmt } from '@/lib/utils';

type Row = { strategy: { name: string; params: Record<string, number> }; metrics: Record<string, number>; trades: number };

export default function ComparePage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set(['ai_scoring', 'ema_cross', 'rsi_meanrev']));
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [interval, setInterval] = useState('1d');
  const [rows, setRows] = useState<Row[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { api.strategies().then(setStrategies); }, []);

  function toggle(n: string) {
    const next = new Set(selected);
    next.has(n) ? next.delete(n) : next.add(n);
    setSelected(next);
  }

  async function run() {
    setLoading(true); setErr(null);
    try {
      const res = await api.compare({
        data: { symbol, interval, source: 'bitget', with_fear_greed: true },
        strategies: [...selected].map(n => ({ name: n, params: {} })),
      });
      setRows(res as Row[]);
    } catch (e: any) { setErr(e.message); } finally { setLoading(false); }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold">Compare strategies</h1>
        <p className="text-slate-400 mt-1">Run multiple strategies against the same dataset side by side.</p>
      </header>

      <Card>
        <div className="grid md:grid-cols-3 gap-4">
          <div><Label>Symbol</Label><Input value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())} /></div>
          <div><Label>Interval</Label>
            <select className="w-full rounded-md border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm"
              value={interval} onChange={e => setInterval(e.target.value)}>
              {['1h', '4h', '1d', '1w'].map(i => <option key={i}>{i}</option>)}
            </select>
          </div>
          <div className="flex items-end"><Button onClick={run} disabled={loading || !selected.size}>{loading ? 'Running…' : 'Compare'}</Button></div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {strategies.map(s => (
            <button key={s.name} onClick={() => toggle(s.name)}
              className={`px-3 py-1.5 rounded-full text-xs border ${selected.has(s.name) ? 'bg-sky-500/20 border-sky-500 text-sky-200' : 'border-slate-700 text-slate-400'}`}>
              {s.name}
            </button>
          ))}
        </div>
        {err && <div className="text-sm text-rose-400 mt-3">{err}</div>}
      </Card>

      {rows && (
        <Card>
          <CardHeader title="Comparison" subtitle={`${rows.length} strategies on ${symbol} ${interval}`} />
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/60 text-slate-400 uppercase text-xs tracking-wider">
                <tr>
                  <th className="text-left px-4 py-3">Strategy</th>
                  <th className="text-right px-4 py-3">Return</th>
                  <th className="text-right px-4 py-3">Sharpe</th>
                  <th className="text-right px-4 py-3">Sortino</th>
                  <th className="text-right px-4 py-3">Max DD</th>
                  <th className="text-right px-4 py-3">Win rate</th>
                  <th className="text-right px-4 py-3">Profit factor</th>
                  <th className="text-right px-4 py-3">Trades</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {rows.map(r => (
                  <tr key={r.strategy.name}>
                    <td className="px-4 py-2">{r.strategy.name}</td>
                    <td className={`px-4 py-2 text-right ${r.metrics.total_return >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>{fmt.pct(r.metrics.total_return)}</td>
                    <td className="px-4 py-2 text-right">{fmt.num(r.metrics.sharpe_ratio)}</td>
                    <td className="px-4 py-2 text-right">{fmt.num(r.metrics.sortino_ratio)}</td>
                    <td className="px-4 py-2 text-right text-rose-300">{fmt.pct(r.metrics.max_drawdown)}</td>
                    <td className="px-4 py-2 text-right">{fmt.pct(r.metrics.win_rate, 1)}</td>
                    <td className="px-4 py-2 text-right">{fmt.num(r.metrics.profit_factor)}</td>
                    <td className="px-4 py-2 text-right">{r.trades}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
