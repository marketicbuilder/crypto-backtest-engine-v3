'use client';
import { useEffect, useState } from 'react';
import { api, type Strategy } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/card';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function StrategiesPage() {
  const [list, setList] = useState<Strategy[]>([]);
  useEffect(() => { api.strategies().then(setList); }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">Strategy library</h1>
          <p className="text-slate-400 mt-1">Bundled plug-ins are auto-discovered from the backend's
            <code className="text-sky-300 mx-1">@register</code> decorator.</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {list.map(s => (
          <Card key={s.name}>
            <CardHeader title={s.name} subtitle="Default parameters" />
            <dl className="text-sm grid grid-cols-2 gap-y-1.5 gap-x-3">
              {Object.entries(s.params).map(([k, v]) => (
                <div key={k} className="contents">
                  <dt className="text-slate-400">{k}</dt>
                  <dd className="text-slate-100 text-right">{String(v)}</dd>
                </div>
              ))}
            </dl>
            <Link href={`/backtests?strategy=${s.name}`} className="block mt-4">
              <Button variant="secondary" className="w-full">Configure & backtest</Button>
            </Link>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader title="Adding a new strategy" />
        <pre className="text-xs bg-slate-950/60 rounded-md p-4 overflow-x-auto scrollbar-thin"><code>{`# backend/app/strategies/my_strategy.py
from dataclasses import dataclass, field
from .base import Signal, register

@dataclass
class MyStrategy:
    name: str = "my_strategy"
    params: dict = field(default_factory=lambda: {"length": 20})
    def prepare(self, df): return df
    def decide(self, row, position):
        return Signal("hold", 50, "no logic yet")

@register("my_strategy")
def _factory(**params): return MyStrategy()
`}</code></pre>
        <p className="text-xs text-slate-500 mt-3">Add an import in
          <code className="text-sky-300 mx-1">app/strategies/__init__.py</code> and it appears in this list.</p>
      </Card>
    </div>
  );
}
