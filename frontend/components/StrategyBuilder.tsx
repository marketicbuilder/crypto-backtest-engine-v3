"use client";

import { useState } from "react";

type Tier = "visual" | "code" | "agent";
type Indicator = "rsi" | "ema_cross" | "macd" | "bbands";
type Step = 1 | 2 | 3 | 4;

interface VisualConfig {
  name: string;
  indicator: Indicator;
  params: Record<string, number>;
  stop_loss_pct: number;
  take_profit_pct: number;
}

interface SubmitResult {
  status: "registered" | "error";
  name?: string;
  message?: string;
}

const INDICATORS = [
  {
    id: "rsi" as Indicator,
    label: "RSI Mean Reversion",
    description: "Buy oversold, sell overbought using the Relative Strength Index.",
    params: [
      { key: "length",     label: "RSI Period",          default: 14, min: 2,  max: 50, step: 1 },
      { key: "buy_below",  label: "Buy when RSI below",  default: 30, min: 5,  max: 49, step: 1 },
      { key: "sell_above", label: "Sell when RSI above", default: 70, min: 51, max: 95, step: 1 },
    ],
  },
  {
    id: "ema_cross" as Indicator,
    label: "EMA Crossover",
    description: "Buy when fast EMA crosses above slow EMA, sell on the reverse.",
    params: [
      { key: "fast", label: "Fast EMA period", default: 9,  min: 2, max: 50,  step: 1 },
      { key: "slow", label: "Slow EMA period", default: 21, min: 5, max: 200, step: 1 },
    ],
  },
  {
    id: "macd" as Indicator,
    label: "MACD Signal Cross",
    description: "Trade MACD line crossovers with the signal line.",
    params: [
      { key: "fast",   label: "Fast period",   default: 12, min: 2, max: 50,  step: 1 },
      { key: "slow",   label: "Slow period",   default: 26, min: 5, max: 200, step: 1 },
      { key: "signal", label: "Signal period", default: 9,  min: 2, max: 50,  step: 1 },
    ],
  },
  {
    id: "bbands" as Indicator,
    label: "Bollinger Bands Bounce",
    description: "Buy at lower band, sell at upper band during ranging markets.",
    params: [
      { key: "length", label: "Period",             default: 20, min: 5, max: 100, step: 1   },
      { key: "std",    label: "Std dev multiplier", default: 2,  min: 1, max: 4,   step: 0.5 },
    ],
  },
];

const TEMPLATE = `from dataclasses import dataclass, field
from app.strategies.base import Signal, register

@dataclass
class MyStrategy:
    name: str = "my_strategy"
    params: dict = field(default_factory=lambda: {"length": 20})
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.10

    def prepare(self, df):
        return df

    def decide(self, df, position):
        return Signal("hold", 50, "no logic yet")

@register("my_strategy")
def _factory(**params):
    return MyStrategy(**params)`;

function SliderInput({ paramDef, value, onChange }: {
  paramDef: { key: string; label: string; min: number; max: number; step: number };
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="mb-5">
      <div className="flex justify-between mb-1.5">
        <label className="text-xs text-slate-400">{paramDef.label}</label>
        <span className="text-xs font-bold text-sky-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">{value}</span>
      </div>
      <input type="range" min={paramDef.min} max={paramDef.max} step={paramDef.step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-sky-500 cursor-pointer" />
      <div className="flex justify-between mt-1">
        <span className="text-[10px] text-slate-600">{paramDef.min}</span>
        <span className="text-[10px] text-slate-600">{paramDef.max}</span>
      </div>
    </div>
  );
}

function CopyBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="relative">
      <pre className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-sky-300 font-mono overflow-x-auto whitespace-pre-wrap break-all leading-relaxed">{code}</pre>
      <button onClick={() => { navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
        className="absolute top-2 right-2 px-2.5 py-1 bg-slate-800 border border-slate-700 rounded text-[11px] text-slate-400 hover:text-slate-200 transition-colors">
        {copied ? "✓" : "Copy"}
      </button>
    </div>
  );
}

function ResultBanner({ result, onReset }: { result: SubmitResult; onReset: () => void }) {
  const ok = result.status === "registered";
  return (
    <div className={`rounded-xl p-6 text-center border ${ok ? "bg-emerald-950/40 border-emerald-800" : "bg-red-950/40 border-red-900"}`}>
      <div className="text-4xl mb-3">{ok ? "🚀" : "❌"}</div>
      <p className={`font-bold mb-1 ${ok ? "text-emerald-400" : "text-red-400"}`}>
        {ok ? `"${result.name}" registered!` : "Registration failed"}
      </p>
      <p className="text-sm text-slate-500 mb-4">
        {ok ? "It now appears in your Strategies list. Configure & backtest it from there." : result.message}
      </p>
      <button onClick={onReset}
        className="px-5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-sm text-slate-300 transition-colors">
        Add another
      </button>
    </div>
  );
}

function VisualBuilder({ onSubmit, loading }: { onSubmit: (c: VisualConfig) => void; loading: boolean }) {
  const [step, setStep] = useState<Step>(1);
  const [config, setConfig] = useState<VisualConfig>({
    name: "", indicator: "rsi",
    params: Object.fromEntries(INDICATORS[0].params.map((p) => [p.key, p.default])),
    stop_loss_pct: 0.05, take_profit_pct: 0.10,
  });

  const selected = INDICATORS.find((i) => i.id === config.indicator)!;
  const canNext = step === 4 ? config.name.trim().length >= 3 : true;

  const steps = ["Indicator", "Parameters", "Risk", "Save"];

  return (
    <div>
      <div className="flex items-center gap-1 mb-6">
        {steps.map((label, i) => {
          const s = i + 1;
          const done = step > s; const active = step === s;
          return (
            <div key={s} className="flex items-center gap-1 flex-1 last:flex-none">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold border-2 shrink-0 transition-all
                ${done ? "bg-sky-500 border-sky-500 text-white" : active ? "border-sky-500 text-sky-400" : "border-slate-700 text-slate-600"}`}>
                {done ? "✓" : s}
              </div>
              <span className={`text-[11px] hidden sm:block ${active ? "text-slate-400" : "text-slate-600"}`}>{label}</span>
              {s < steps.length && <div className="flex-1 h-px bg-slate-800 mx-1" />}
            </div>
          );
        })}
      </div>

      {step === 1 && (
        <div className="space-y-2.5">
          <p className="text-xs text-slate-500 mb-3">Pick the signal type your strategy will use.</p>
          {INDICATORS.map((ind) => (
            <button key={ind.id} onClick={() => {
              const i = INDICATORS.find((x) => x.id === ind.id)!;
              setConfig((c) => ({ ...c, indicator: ind.id, params: Object.fromEntries(i.params.map((p) => [p.key, p.default])) }));
            }}
              className={`w-full text-left p-4 rounded-xl border transition-all
                ${config.indicator === ind.id ? "bg-sky-950/40 border-sky-700" : "bg-slate-900/40 border-slate-800 hover:border-slate-600"}`}>
              <p className={`text-sm font-semibold mb-1 ${config.indicator === ind.id ? "text-sky-400" : "text-slate-200"}`}>{ind.label}</p>
              <p className="text-xs text-slate-500">{ind.description}</p>
            </button>
          ))}
        </div>
      )}

      {step === 2 && (
        <div>
          <p className="text-xs text-slate-500 mb-4">Tune the <span className="text-slate-300">{selected.label}</span> parameters.</p>
          {selected.params.map((p) => (
            <SliderInput key={p.key} paramDef={p} value={config.params[p.key] ?? p.default}
              onChange={(v) => setConfig((c) => ({ ...c, params: { ...c.params, [p.key]: v } }))} />
          ))}
        </div>
      )}

      {step === 3 && (
        <div>
          <p className="text-xs text-slate-500 mb-4">Set your risk controls. These apply to every trade automatically.</p>
          <SliderInput paramDef={{ key: "sl", label: "Stop loss %", min: 1, max: 20, step: 0.5 }}
            value={Math.round(config.stop_loss_pct * 100 * 2) / 2}
            onChange={(v) => setConfig((c) => ({ ...c, stop_loss_pct: v / 100 }))} />
          <SliderInput paramDef={{ key: "tp", label: "Take profit %", min: 1, max: 50, step: 0.5 }}
            value={Math.round(config.take_profit_pct * 100 * 2) / 2}
            onChange={(v) => setConfig((c) => ({ ...c, take_profit_pct: v / 100 }))} />
          {config.take_profit_pct <= config.stop_loss_pct && (
            <p className="text-xs text-amber-400 bg-amber-950/30 border border-amber-900 rounded-lg px-3 py-2">
              ⚠️ Take profit should exceed stop loss for a positive risk/reward ratio.
            </p>
          )}
        </div>
      )}

      {step === 4 && (
        <div>
          <p className="text-xs text-slate-500 mb-3">Give your strategy a unique name.</p>
          <input type="text" placeholder="e.g. my_rsi_bounce" value={config.name}
            onChange={(e) => setConfig((c) => ({ ...c, name: e.target.value.toLowerCase().replace(/\s+/g, "_") }))}
            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-xl text-slate-200 font-mono text-sm outline-none transition-colors" />
          <p className="text-[10px] text-slate-600 mt-1.5">Spaces become underscores. Lowercase only.</p>
          <div className="mt-4 p-4 bg-slate-900/40 rounded-xl border border-slate-800">
            <p className="text-[10px] uppercase tracking-widest text-slate-600 mb-2">Summary</p>
            <div className="grid grid-cols-2 gap-y-2">
              {[["Indicator", selected.label], ...Object.entries(config.params).map(([k, v]) => [k, String(v)]),
                ["Stop loss", `${(config.stop_loss_pct * 100).toFixed(1)}%`],
                ["Take profit", `${(config.take_profit_pct * 100).toFixed(1)}%`]
              ].map(([k, v]) => (
                <div key={k}><span className="text-[10px] text-slate-600">{k} </span><span className="text-xs text-slate-300 font-semibold">{v}</span></div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-between mt-6 gap-3">
        {step > 1
          ? <button onClick={() => setStep((s) => (s - 1) as Step)} className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-sm text-slate-300 transition-colors">← Back</button>
          : <div />}
        {step < 4
          ? <button onClick={() => setStep((s) => (s + 1) as Step)} className="px-6 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-sm font-semibold transition-colors">Next →</button>
          : <button onClick={() => onSubmit(config)} disabled={!canNext || loading}
              className={`px-6 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 transition-colors
                ${canNext && !loading ? "bg-sky-600 hover:bg-sky-500 text-white" : "bg-slate-800 text-slate-600 cursor-not-allowed"}`}>
              {loading ? <><span className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />Registering…</> : "Save & Register →"}
            </button>}
      </div>
    </div>
  );
}

function CodeEditor({ onSubmit, loading }: { onSubmit: (name: string, code: string) => void; loading: boolean }) {
  const [name, setName] = useState("");
  const [code, setCode] = useState(TEMPLATE);
  const ready = name.trim().length >= 3 && code.length >= 50;

  return (
    <div>
      <p className="text-xs text-slate-500 mb-4">
        Paste your full strategy class. Must use the <code className="text-sky-400 bg-slate-900 px-1 rounded text-[11px]">@register</code> pattern.
      </p>
      <div className="mb-4">
        <label className="text-xs text-slate-500 block mb-1.5">Strategy name (must match your <code className="text-sky-400 text-[11px]">@register</code> key)</label>
        <input type="text" value={name} placeholder="e.g. my_strategy"
          onChange={(e) => setName(e.target.value.toLowerCase().replace(/\s+/g, "_"))}
          className="w-full px-4 py-3 bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-xl text-slate-200 font-mono text-sm outline-none transition-colors" />
      </div>
      <textarea value={code} onChange={(e) => setCode(e.target.value)} rows={16} spellCheck={false}
        className="w-full p-4 bg-slate-950 border border-slate-800 focus:border-sky-800 rounded-xl text-sky-300 font-mono text-xs leading-relaxed resize-y outline-none transition-colors" />
      <p className="text-xs text-slate-600 bg-slate-900/40 border border-slate-800 rounded-lg px-3 py-2 mt-2 mb-4">
        🔒 Blocked: os · subprocess · sys · open() · exec() · eval()
      </p>
      <button onClick={() => onSubmit(name, code)} disabled={!ready || loading}
        className={`w-full py-3 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-colors
          ${ready && !loading ? "bg-sky-600 hover:bg-sky-500 text-white" : "bg-slate-800 text-slate-600 cursor-not-allowed"}`}>
        {loading ? <><span className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />Registering…</> : "Upload & Register Strategy"}
      </button>
    </div>
  );
}

function AgentDocs() {
  return (
    <div className="space-y-5">
      <p className="text-xs text-slate-500">Agents can submit strategies over HTTP. No UI needed — just POST JSON.</p>
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[11px] font-bold text-emerald-400 bg-emerald-950/50 border border-emerald-900 px-2 py-0.5 rounded">POST</span>
          <code className="text-sm text-slate-300">/api/strategies/visual</code>
        </div>
        <CopyBlock code={`{
  "name": "agent_rsi_v1",
  "indicator": "rsi",
  "params": { "length": 14, "buy_below": 28, "sell_above": 72 },
  "stop_loss_pct": 0.04,
  "take_profit_pct": 0.12
}`} />
      </div>
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[11px] font-bold text-emerald-400 bg-emerald-950/50 border border-emerald-900 px-2 py-0.5 rounded">POST</span>
          <code className="text-sm text-slate-300">/api/strategies/code</code>
        </div>
        <CopyBlock code={`{
  "name": "my_strategy",
  "code": "...full Python class string..."
}`} />
      </div>
      <div>
        <p className="text-xs text-slate-500 mb-2">Both endpoints return:</p>
        <CopyBlock code={`{ "status": "registered", "name": "your_strategy_name" }`} />
      </div>
      <div className="p-4 bg-slate-900/40 rounded-xl border border-slate-800">
        <p className="text-[10px] uppercase tracking-widest text-slate-600 mb-3">Agent workflow</p>
        {[["1","POST /api/strategies/visual","Register"],["2","POST /api/backtests/run","Backtest"],["3","GET /api/backtests/{id}","Poll results"],["4","Iterate params","Optimise"]].map(([n,e,d]) => (
          <div key={n} className="flex items-center gap-3 mb-2 last:mb-0">
            <div className="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center text-[10px] text-slate-500 shrink-0">{n}</div>
            <code className="text-xs text-sky-400 flex-1">{e}</code>
            <span className="text-xs text-slate-600">{d}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function StrategyBuilder() {
  const [tier, setTier]       = useState<Tier>("visual");
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState<SubmitResult | null>(null);

  const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "";

  const post = async (url: string, body: object) => {
    const res  = await fetch(`${BACKEND}${url}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail ?? "Unknown error");
    return data;
  };

  const handleVisual = async (config: VisualConfig) => {
    setLoading(true);
    try   { const d = await post("/api/strategies/visual", config); setResult({ status: "registered", name: d.name }); }
    catch (e) { setResult({ status: "error", message: (e as Error).message }); }
    finally   { setLoading(false); }
  };

  const handleCode = async (name: string, code: string) => {
    setLoading(true);
    try   { const d = await post("/api/strategies/code", { name, code }); setResult({ status: "registered", name: d.name }); }
    catch (e) { setResult({ status: "error", message: (e as Error).message }); }
    finally   { setLoading(false); }
  };

  const TABS = [
    { id: "visual" as Tier, icon: "🎛️", label: "Builder",   sub: "No coding required" },
    { id: "code"   as Tier, icon: "💻", label: "Code",       sub: "Paste Python class"  },
    { id: "agent"  as Tier, icon: "🤖", label: "Agent API",  sub: "REST reference"      },
  ];

  return (
    <div className="min-h-screen flex items-start justify-center px-4 py-10">
      <div className="w-full max-w-lg">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">⚡ Add a Strategy</h1>
          <p className="text-sm text-slate-500 mt-1">Build visually, paste code, or POST via API — all three register to the same backtest engine.</p>
        </div>

        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl overflow-hidden">
          <div className="flex border-b border-slate-800">
            {TABS.map((t) => (
              <button key={t.id} onClick={() => { setTier(t.id); setResult(null); }}
                className={`flex-1 py-3 px-2 flex flex-col items-center gap-0.5 transition-colors border-b-2
                  ${tier === t.id ? "border-sky-500 text-slate-200 bg-slate-900/60" : "border-transparent text-slate-600 hover:text-slate-400"}`}>
                <span className="text-base">{t.icon}</span>
                <span className="text-xs font-semibold">{t.label}</span>
              </button>
            ))}
          </div>
          <div className="p-5">
            {result
              ? <ResultBanner result={result} onReset={() => setResult(null)} />
              : <>
                  {tier === "visual" && <VisualBuilder onSubmit={handleVisual} loading={loading} />}
                  {tier === "code"   && <CodeEditor    onSubmit={handleCode}   loading={loading} />}
                  {tier === "agent"  && <AgentDocs />}
                </>}
          </div>
        </div>

        <p className="text-center text-[11px] text-slate-700 mt-4">
          Powered by Bitget API · Strategies register live without server restart
        </p>
      </div>
    </div>
  );
}
