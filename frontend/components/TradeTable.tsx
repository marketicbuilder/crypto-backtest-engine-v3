import { cn, fmt } from '@/lib/utils';
import type { Trade } from '@/lib/api';

export function TradeTable({ trades }: { trades: Trade[] }) {
  if (!trades.length) return <div className="text-slate-500 text-sm p-4">No trades.</div>;
  return (
    <div className="rounded-xl border border-slate-800 overflow-x-auto scrollbar-thin max-h-[480px]">
      <table className="w-full text-xs min-w-[820px]">
        <thead className="bg-slate-900/60 text-slate-400 uppercase tracking-wider sticky top-0">
          <tr>
            <th className="text-left px-3 py-2">Entry</th>
            <th className="text-left px-3 py-2">Exit</th>
            <th className="text-left px-3 py-2">Side</th>
            <th className="text-right px-3 py-2">Entry $</th>
            <th className="text-right px-3 py-2">Exit $</th>
            <th className="text-right px-3 py-2">Qty</th>
            <th className="text-right px-3 py-2">PnL</th>
            <th className="text-right px-3 py-2">PnL %</th>
            <th className="text-right px-3 py-2">Score</th>
            <th className="text-left px-3 py-2">Reason exit</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/70">
          {trades.map((t, i) => {
            const pnlCls = t.pnl >= 0 ? 'text-emerald-300' : 'text-rose-300';
            return (
              <tr key={i} className="hover:bg-slate-900/40">
                <td className="px-3 py-1.5">{t.entry_time.slice(0, 10)}</td>
                <td className="px-3 py-1.5">{t.exit_time.slice(0, 10)}</td>
                <td className={cn('px-3 py-1.5', t.side === 'long' ? 'text-emerald-400' : 'text-rose-400')}>{t.side}</td>
                <td className="px-3 py-1.5 text-right">{fmt.money(t.entry_price, 2)}</td>
                <td className="px-3 py-1.5 text-right">{fmt.money(t.exit_price, 2)}</td>
                <td className="px-3 py-1.5 text-right">{t.qty.toFixed(4)}</td>
                <td className={cn('px-3 py-1.5 text-right', pnlCls)}>{fmt.money(t.pnl, 2)}</td>
                <td className={cn('px-3 py-1.5 text-right', pnlCls)}>{fmt.pct(t.pnl_pct)}</td>
                <td className="px-3 py-1.5 text-right">{t.score.toFixed(0)}</td>
                <td className="px-3 py-1.5 text-slate-400">{t.reason_exit}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function exportCSV(trades: Trade[]): string {
  const header = ['entry_time', 'exit_time', 'side', 'entry_price', 'exit_price',
                  'qty', 'pnl', 'pnl_pct', 'fees', 'score', 'reason_entry', 'reason_exit'];
  const rows = trades.map(t => header.map(k => JSON.stringify((t as any)[k] ?? '')).join(','));
  return [header.join(','), ...rows].join('\n');
}
