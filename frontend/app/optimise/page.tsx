'use client';
import { useState } from 'react';
import { Card, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input, Label } from '@/components/ui/input';
import { api } from '@/lib/api';
import { fmt } from '@/lib/utils';

function parseList(s: string): number[] {
  return s.split(',').map(t => +t.trim()).filter(n => !Number.isNaN(n));
}

export default function OptimisePage() {
  const [strategy, setStrategy] = useState('ema_cross');
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [objective, setObjective] = useState<'sharpe' | 'calmar' | 'return'>('sharpe');
  const [grid, setGrid] = useState<Record<string, string>>({ fast: '9,12,20,30', slow: '26,50,100,200' });
  const [resp, setResp] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setLoading(true); setErr(null);
    try {
      const r = await api.optimise({
        data: { symbol, interval: '1d', source: 'bitget', with_fear_greed: true },
        strategy_name: strategy,
        param_grid: Object.fromEntries(Object.entries(grid).map(([k, v]) => [k, parseList(v)])),
        objective,
      });
      setResp(r);
    } catch (e: any) { setErr(e.message); } finally { setLoading(false); }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold">Parameter optimisation</h1>
        <p className="text-slate-400 mt-1">Grid-search over strategy parameters and rank by objective.</p>
      </header>

      <Card>
        <div className="grid md:grid-cols-4 gap-4">
          <div><Label>Strategy</Label>
            <select className="w-full rounded-md border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm"
              value={strategy} onChange={e => setStrategy(e.target.value)}>
              <option value="ema_cross">ema_cross</option>
              <option value="rsi_meanrev">rsi_meanrev</option>
              <option value="ai_scoring">ai_scoring</option>
            </select>
          </div>
          <div><Label>Symbol</Label><Input value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())} /></div>
          <div><Label>Objective</Label>
            <select className="w-full rounded-md border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm"
              value={objective} onChange={e => setObjective(e.target.value as any)}>
              <option value="sharpe">sharpe</option>
              <option value="calmar">calmar</option>
              <option value="return">return</option>
            </select>
          </div>
          <div className="flex items-end"><Button onClick={run} disabled={loading}>{loading ? 'Searching…' : 'Run grid search'}</Button></div>
        </div>

        <div className="mt-4 grid md:grid-cols-2 gap-4">
          {Object.entries(grid).map(([k, v]) => (
            <div key={k}>
              <Label>{k} values (comma-separated)</Label>
              <Input value={v} onChange={e => setGrid({ ...grid, [k]: e.target.value })} />
            </div>
          ))}
        </div>
        {err && <div className="text-sm text-rose-400 mt-3">{err}</div>}
      </Card>

      {resp && (
        <>
          <Card>
            <CardHeader title="Best configuration" subtitle={`objective: ${objective}`} />
            <div className="text-sm mb-2 text-slate-400">params: <span className="text-slate-100">{JSON.stringify(resp.best_params)}</span></div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Kpi label="Return" v={fmt.pct(resp.best_metrics.total_return)} ok={resp.best_metrics.total_return >= 0} />
              <Kpi label="Sharpe" v={fmt.num(resp.best_metrics.sharpe_ratio)} ok={resp.best_metrics.sharpe_ratio >= 1} />
              <Kpi label="Max DD" v={fmt.pct(resp.best_metrics.max_drawdown)} ok={resp.best_metrics.max_drawdown > -0.2} />
              <Kpi label="Win rate" v={fmt.pct(resp.best_metrics.win_rate, 1)} ok={resp.best_metrics.win_rate >= 0.5} />
            </div>
          </Card>

          <Card>
            <CardHeader title="All configurations" subtitle={`${resp.table.length} rows`} />
            <div className="overflow-x-auto scrollbar-thin max-h-[480px]">
              <table className="w-full text-xs">
                <thead className="bg-slate-900/60 text-slate-400 uppercase tracking-wider sticky top-0">
                  <tr>
                    {Object.keys(resp.table[0] || {}).filter(k => k !== 'drawdown_series').map(k =>
                      <th key={k} className="text-right px-3 py-2">{k}</th>)}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {resp.table.slice(0, 200).map((row: any, i: number) => (
                    <tr key={i}>
                      {Object.entries(row).filter(([k]) => k !== 'drawdown_series').map(([k, v]: any) => (
                        <td key={k} className="text-right px-3 py-1.5">{typeof v === 'number' ? v.toFixed(4) : String(v)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function Kpi({ label, v, ok }: { label: string; v: string; ok: boolean }) {
  return (
    <div className="rounded-md border border-slate-800 p-3">
      <div className="text-[11px] uppercase text-slate-500">{label}</div>
      <div className={`text-lg font-semibold mt-0.5 ${ok ? 'text-emerald-300' : 'text-rose-300'}`}>{v}</div>
    </div>
  );
}
