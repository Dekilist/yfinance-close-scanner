# YFinance V3 Pattern Scanner

This is a read-only Python GUI for scanning U.S. stocks with `yfinance` daily market data.

It does not trade, unlock trading, store passwords, connect to FutuOpenD, or place orders.

## Main File

Run the yfinance version with:

```powershell
python yfinance_prototype_scanner.py
```

The older Futu/OpenD scanner is still in `afterhours_scanner.py`, but this README describes the yfinance version.

## What It Checks

The scanner maps the requirement document into four independent selectable traits:

- `+10% high-turnover mover`
  - Close-to-close gain is at least `10%`.
  - Mover ratio is at least `2`.
  - Latest daily turnover is at least `50,000,000`.
  - Close price is at least `$3`.
  - Market cap is at least `100,000,000`.

- `EMA5/10/20 bullish for 5D+`
  - EMA5 >= EMA10 >= EMA20 for at least `5` consecutive trading days.
  - Daily turnover is at least `20,000,000` during that period.
  - Close price is at least `$3`.
  - Market cap is at least `500,000,000`.

- `3D+ tight 5% price range`
  - Recent high/low range is within `5%` for at least `3` trading days.
  - Daily turnover is at least `20,000,000` during that period.
  - Close price is at least `$3`.
  - Market cap is at least `500,000,000`.

- `20D high-turnover box breakout`
  - The latest `20` trading days ending on the current/latest day form the measured price box.
  - Box width is calculated as `box_high / box_low - 1`.
  - Box width must be no more than `15%`.
  - The latest close must break above the upper edge formed by the earlier days in that box window.
  - Latest turnover must be at least `1.5` times the prior 5-day average turnover.
  - Latest turnover must be at least `30,000,000`.
  - Market cap is at least `500,000,000`.

Each trait is independent. A stock can match one trait, multiple traits, or none. Use `Any Selected` to show stocks matching at least one selected trait, or `All Selected` to require every selected trait.

## Setup

1. Install Python.
2. Install the yfinance dependencies:

```powershell
python -m pip install yfinance pandas
```

3. Run the GUI:

```powershell
python yfinance_prototype_scanner.py
```

No FutuOpenD login, Futu quote permission, or Futu historical candlestick quota is required for this version.

## How To Use

- Leave `Source` as `U.S. Stock Universe` to load U.S. listed symbols from NASDAQ Trader symbol directories.
- Use `Manual Symbols` if you only want to test a short list such as `AAPL, TSLA, NVDA`.
- `Close Year` is set to the current year automatically.
- `Close Month` and `Close Day` default to today's month and day.
- If `Close Month` and `Close Day` are both blank, the scanner still defaults to today's date.
- Choose `Close Month` and `Close Day` from the dropdowns to scan as of that close. If the selected date is not a trading day, the scanner uses the latest available trading bar on or before that date.
- Set `Max Symbols` to `0` to scan the whole loaded universe, or use a smaller number while testing.
- Adjust the V3 thresholds in the left sidebar.
- Select one or more traits.
- Click `Run Scan`.
- Click `Export CSV` after a scan to save the current results.
- Open the `News` tab after a scan to load recent Yahoo/yfinance news for the matched symbols.
- If there are no scan results yet, the `News` tab uses the manually entered symbols instead.
- Double-click a news row, or select it and click `Open Link`, to open the source article.
- Click `Export News CSV` to save the loaded news rows.
- Use the `Chinese` / `English` language button to switch the interface language.

## News Tab

The `News` tab is designed as a quick risk and catalyst companion to the scanner results. It loads recent Yahoo/yfinance news for the selected symbols and classifies headlines into practical buckets:

- `Insider/Executive`: examples include insider sales, senior executive stock sales, Form 4-style wording, CEO/CFO/director headlines.
- `Incident/Risk`: examples include outages, cyber incidents, recalls, accidents, shutdowns, crashes, and other operational events.
- `Legal/Investigation`: lawsuits, settlements, SEC/DOJ/regulator probes, fraud, antitrust, and similar risk items.
- `Earnings/Guidance`, `Deal/M&A`, `Analyst/Rating`, `Macro/Policy`, and `General`.

The categories are keyword-based helpers, not legal or financial conclusions. Yahoo/yfinance news may miss SEC filings, insider transactions, local incidents, paywalled articles, or smaller-company updates. For complete insider sale monitoring, add a licensed SEC/Form 4 or corporate-actions data source later.

## Data Notes

This prototype uses `yfinance`, which retrieves Yahoo Finance data. It is useful for prototyping and research, but it is not an official market data feed.

Important limitations:

- The latest daily bar may be delayed, adjusted, incomplete, or unavailable.
- Yahoo/yfinance can throttle requests, especially when scanning the full U.S. universe.
- Yahoo/yfinance news coverage varies by symbol and does not guarantee complete recent news or insider-transaction coverage.
- Market cap can be missing for some symbols. The app has an `Allow missing market cap` option, but turning it on makes market-cap filters less strict.
- Mover ratio is approximated as latest daily volume divided by the previous 20-day average volume. It is not Futu's real-time volume ratio.
- Turnover is approximated as `Close * Volume`.
- The U.S. stock universe is filtered from NASDAQ Trader symbol files and excludes many ETFs, warrants, units, rights, preferreds, notes, and obvious non-common-stock instruments.

For more reliable production scanning, use a paid data provider with licensed historical daily OHLCV, market cap, and full-symbol coverage.
