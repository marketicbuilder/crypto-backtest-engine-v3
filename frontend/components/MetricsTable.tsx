import { cn, fmt } from '@/lib/utils';

export function KpiCard({ label, value, hint, good }: {
  label: string; value: string; hint?: string; good?: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <div className="text-[11px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className={cn(
        'text-2xl font-semibold mt-1',
        good == null ? 'text-slate-100' : good ? 'text-emerald-300' : 'text-rose-300',
      )}>{value}</div>
      {hint && <div className="text-[11px] text-slate-500 mt-1">{hint}</div>}
    </div>
  );
}

export function MetricsTable({ m, starting }: { m: Record<string, number>; starting: number }) {
  const rows: Array<[string, string, string]> = [
    ['Starting balance', fmt.money(starting), ''],
    ['Final balance', fmt.money(m.final_balance), 'after fees & slippage'],
    ['Total return', fmt.pct(m.total_return), 'cumulative'],
    ['Annual return', fmt.pct(m.annual_return), 'CAGR'],
    ['Sharpe ratio', fmt.num(m.sharpe_ratio), 'risk-adjusted return'],
    ['Sortino ratio', fmt.num(m.sortino_ratio), 'downside-only volatility'],
    ['Calmar ratio', fmt.num(m.calmar_ratio), 'CAGR ÷ |max DD|'],
    ['Max drawdown', fmt.pct(m.max_drawdown), 'worst peak-to-trough'],
    ['Profit factor', fmt.num(m.profit_factor), 'gross profit ÷ gross loss'],
    ['Win rate', fmt.pct(m.win_rate, 1), ''],
    ['Loss rate', fmt.pct(m.loss_rate, 1), ''],
    ['Average win', fmt.money(m.average_win, 2), ''],
    ['Average loss', fmt.money(m.average_loss, 2), ''],
    ['Risk / reward', fmt.num(m.risk_reward), 'avg-win ÷ |avg-loss|'],
    ['Total trades', String(m.total_trades ?? '—'), ''],
    ['Longest win streak', String(m.longest_win_streak ?? '—'), ''],
    ['Longest loss streak', String(m.longest_loss_streak ?? '—'), ''],
  ];
  return (
    <div className="rounded-xl border border-slate-800 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-900/60 text-slate-400 uppercase text-xs tracking-wider">
          <tr><th className="text-left px-4 py-3">Metric</th>
              <th className="text-right px-4 py-3">Value</th>
              <th className="text-left px-4 py-3 hidden md:table-cell">Notes</th></tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {rows.map(([k, v, n]) => (
            <tr key={k}>
              <td className="px-4 py-2 text-slate-200">{k}</td>
              <td className="px-4 py-2 text-right font-medium">{v}</td>
              <td className="px-4 py-2 text-slate-500 hidden md:table-cell">{n}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
