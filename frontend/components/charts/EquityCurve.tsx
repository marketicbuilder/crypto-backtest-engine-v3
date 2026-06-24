'use client';
import { createChart, ColorType, IChartApi, ISeriesApi, Time } from 'lightweight-charts';
import { useEffect, useRef } from 'react';

export function EquityCurve({ data }: { data: { t: string; v: number }[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = createChart(ref.current, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: 'rgba(148,163,184,0.08)' }, horzLines: { color: 'rgba(148,163,184,0.08)' } },
      timeScale: { borderColor: '#1e293b' },
      rightPriceScale: { borderColor: '#1e293b' },
    });
    chartRef.current = chart;
    const area = chart.addAreaSeries({
      lineColor: '#38bdf8', topColor: 'rgba(56,189,248,0.35)', bottomColor: 'rgba(56,189,248,0.05)', lineWidth: 2,
    });
    area.setData(data.map(p => ({ time: p.t.slice(0,10) as Time, value: p.v })));
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [data]);
  return <div ref={ref} className="w-full h-[260px]" />;
}

export function DrawdownChart({ data }: { data: { t: string; v: number }[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = createChart(ref.current, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: 'rgba(148,163,184,0.08)' }, horzLines: { color: 'rgba(148,163,184,0.08)' } },
    });
    const area = chart.addAreaSeries({
      lineColor: '#f43f5e', topColor: 'rgba(244,63,94,0.30)', bottomColor: 'rgba(244,63,94,0.05)', lineWidth: 1,
    });
    area.setData(data.map(p => ({ time: p.t.slice(0,10) as Time, value: p.v })));
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [data]);
  return <div ref={ref} className="w-full h-[220px]" />;
}
