import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }

export const fmt = {
  pct: (v: number | null | undefined, d = 2) =>
    v == null || !isFinite(v) ? '—' : `${(v * 100).toFixed(d)}%`,
  num: (v: number | null | undefined, d = 2) =>
    v == null || !isFinite(v) ? '—' : v.toFixed(d),
  money: (v: number | null | undefined, d = 0) =>
    v == null ? '—' : '$' + v.toLocaleString(undefined, { maximumFractionDigits: d, minimumFractionDigits: d }),
};
