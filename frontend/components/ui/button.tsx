'use client';
import { cn } from '@/lib/utils';
import { forwardRef, ButtonHTMLAttributes } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
const VARIANTS: Record<Variant, string> = {
  primary:   'bg-sky-500 hover:bg-sky-400 text-slate-950 font-medium',
  secondary: 'bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700',
  ghost:     'hover:bg-slate-800/50 text-slate-300',
  danger:    'bg-rose-600 hover:bg-rose-500 text-white',
};

export const Button = forwardRef<HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: 'sm'|'md'|'lg' }>(
  function Button({ className, variant = 'primary', size = 'md', ...props }, ref) {
    const sz = size === 'sm' ? 'px-3 py-1.5 text-xs' : size === 'lg' ? 'px-5 py-3 text-base' : 'px-4 py-2 text-sm';
    return (
      <button ref={ref} className={cn(
        'inline-flex items-center justify-center rounded-md transition',
        'disabled:opacity-50 disabled:pointer-events-none',
        VARIANTS[variant], sz, className,
      )} {...props} />
    );
  }
);
