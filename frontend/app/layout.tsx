import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'AI Crypto Backtest',
  description: 'Test AI trading strategies on historical crypto data.',
};

const nav = [
  { href: '/', label: 'Dashboard' },
  { href: '/strategies', label: 'Strategies' },
  { href: '/backtests', label: 'Backtests' },
  { href: '/compare', label: 'Compare' },
  { href: '/optimise', label: 'Optimise' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <div className="min-h-screen flex flex-col">
          <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur sticky top-0 z-30">
            <div className="max-w-7xl mx-auto px-6 h-14 flex items-center gap-8">
              <Link href="/" className="font-semibold text-sky-300">⟁ AI Backtest</Link>
              <nav className="flex items-center gap-5 text-sm text-slate-300">
                {nav.map(n => (
                  <Link key={n.href} href={n.href} className="hover:text-white">{n.label}</Link>
                ))}
              </nav>
              <div className="ml-auto text-xs text-slate-500">Powered by Bitget API</div>
            </div>
          </header>
          <main className="flex-1 max-w-7xl mx-auto px-6 py-8 w-full">{children}</main>
          <footer className="border-t border-slate-800/80 text-xs text-slate-500 py-4 text-center">
            Built with Next.js · FastAPI · Bitget API · TradingView Lightweight Charts
          </footer>
        </div>
      </body>
    </html>
  );
}
