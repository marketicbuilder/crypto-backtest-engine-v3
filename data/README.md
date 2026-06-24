# Sample datasets

| File              | Source  | Symbol   | Interval | Range                  |
|-------------------|---------|----------|----------|------------------------|
| `btcusdt_1d.csv`  | Binance | BTC/USDT | 1d       | last 5 years (rolling) |

Loaded by `app.data.loader.load_csv`.  To regenerate:

```bash
python -c "from app.data.providers.binance import fetch_ohlcv; \
           fetch_ohlcv('BTCUSDT','1d').to_csv('data/btcusdt_1d.csv')"
```
