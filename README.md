# Futu After-Hours Pattern Scanner

This is a read-only Python GUI for scanning U.S. stocks by after-hours activity plus the technical traits from the requirement document.

It does not trade, unlock trading, store passwords, or place orders.

## What It Checks

The `Traits` tab maps the document into five selectable checks:

- High-volume surge: volume ratio at least `2`, turnover at least `50,000,000`, price at least `5`, and daily gain above the configured threshold.
- 20D box breakout: price breaks above the prior 20 trading day high after a consolidation box.
- Daily+weekly EMA tight bullish: EMA5 > EMA10 > EMA20 on both daily and weekly views, with EMA spread within `5%`.
- Daily EMA bullish 5D+: daily EMA5 > EMA10 > EMA20 for at least one trading week.
- Near EMA20/50/200: current after-hours price is within the configured percentage of EMA20, EMA50, or EMA200.

You can choose `Any Selected` or `All Selected` depending on how strict the scan should be.

## Setup

1. Install and start `FutuOpenD`.
2. Log in with the Futubull/Futu account in `FutuOpenD`.
3. Install Python 3.11 or 3.12.
4. Install the SDK:

```powershell
python -m pip install -r requirements.txt
```

5. Run the GUI:

```powershell
python afterhours_scanner.py
```

## How To Use

- Keep `OpenD Host` as `127.0.0.1` and `OpenD Port` as `11111` unless you changed OpenD settings.
- Enter a small manual list like `AAPL, TSLA, NVDA`, or clear the symbols box to scan the U.S. stock universe.
- Use the `Scan` tab for after-hours filters such as active after-hours volume, after-hours price, after-hours percentage move, and gainers/losers.
- Use the `Traits` tab to select the technical characteristics and tune thresholds.
- Click `Dad Preset` to reset the technical thresholds to the document defaults.
- Click `Export CSV` after a scan to save the result table.

## Important Limits

The app runs a two-stage scan:

1. `get_market_snapshot([...])` scans after-hours fields in batches.
2. `request_history_kline(...)` checks daily/weekly EMA and breakout traits for the top snapshot candidates.

The second stage uses historical candlestick quota, so keep `Max Tech Checks` modest while testing. Futu market data still depends on quote permissions and API quotas. U.S. quote access generally covers NYSE, NYSE-American, and Nasdaq equities/ETFs; OTC securities are unsupported in the Futu OpenAPI quote permission docs.
