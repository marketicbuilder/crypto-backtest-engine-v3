import { cn } from '@/lib/utils';
import { InputHTMLAttributes, forwardRef } from 'react';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return (
      <input ref={ref} className={cn(
        'w-full rounded-md border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm text-slate-100',
        'placeholder:text-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500',
        className,
      )} {...props} />
    );
  }
);

export function Label({ children, className }: { children: React.ReactNode; className?: string }) {
  return <label className={cn('text-xs uppercase tracking-wider text-slate-400 block mb-1', className)}>{children}</label>;
}
