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
- Open the `News` tab to load the ten requested company and market-wide news categories.
- `Tech Symbols` limits the combined scan-result and manually entered symbols used for extra company-specific searches. Broad technology searches run independently of this list.
- `Items / Search` controls the maximum result count for each company or topic search.
- `News Range (Days)` is a dropdown with `1`, `3`, `5`, `7`, `14`, `30`, `60`, and `90` days. The default is `5`.
- The range counts calendar dates inclusively from today. For example, selecting `5` includes today and the previous four dates. The completed status shows the exact start and end dates.
- Use the category menu to show all news or one of the ten categories. Export follows the visible category filter.
- The visible `Main Idea / Summary` column uses a source-supplied summary when available and falls back to the headline when none is supplied.
- In English mode, headlines and summaries remain in their original language. In Chinese mode, both are translated into Simplified Chinese in a background thread and cached for the session. Switching back to English restores both originals immediately.
- Double-click a news row, or select it and click `Open Article`, to open the hidden source URL.
- Click `Export News CSV` to save the loaded news rows.
- Use the `Chinese` / `English` language button to switch the interface language.

## News Tab

The `News` tab implements these ten independent categories:

1. `Tech Company Updates`: U.S.-listed technology companies releasing new technology, new products, executive insider purchases/increased holdings, or new business models. Capacity increases, company buybacks, partnerships, and management appointments/departures do not qualify by themselves.
2. `Tech Events`: important technology conferences, exhibitions, forums, summits, and keynotes.
3. `U.S./China Industry Policy`: new industrial policies, subsidies, funding plans, and export controls from the United States or China.
4. `Geopolitics/Trade`: wars, sanctions, counter-sanctions, export bans, and tariff or trade-war escalation.
5. `Executive/Investor Views`: new interviews, articles, letters, warnings, predictions, and outlooks from major-company executives or well-known investors.
6. `Investment Bank Research`: industry and strategy research from Goldman Sachs, Morgan Stanley, JPMorgan, Bank of America, and Citi.
7. `SEC Rules`: new SEC rules, regulations, proposals, standards, and guidance.
8. `Exchange Rules`: new NYSE, Nasdaq, Cboe, listing, and trading rules.
9. `Federal Reserve`: Federal Reserve and FOMC decisions, meetings, policy, and rate news.
10. `Investment Hot Topics`: themes currently receiving attention in investing and stock-market coverage.

Coverage is expanded for `Tech Company Updates`, `Executive/Investor Views`, and `Investment Bank Research`. The loader combines broad Google News RSS searches with Yahoo and company-specific searches. Broad technology results must match a company in Yahoo's U.S.-exchange Technology, Electronic Gaming & Multimedia, or Internet Content & Information universe. Official company pages and established financial sources rank ahead of secondary coverage.

Cross-source duplicates are grouped by company, date, normalized event wording, and headline similarity. Only the preferred-source version of the same event is displayed, even when publishers use different titles.

These categories are research helpers, not legal or financial conclusions. Public search feeds cannot guarantee complete coverage of company releases, paywalled bank research, executive comments, or breaking events. Production-grade monitoring would still need direct company, SEC, exchange, government, and licensed research/news feeds.

## Data Notes

This prototype uses `yfinance`, which retrieves Yahoo Finance data. It is useful for prototyping and research, but it is not an official market data feed.

Important limitations:

- The latest daily bar may be delayed, adjusted, incomplete, or unavailable.
- Yahoo/yfinance can throttle requests, especially when scanning the full U.S. universe.
- Yahoo and Google News RSS coverage varies and does not guarantee complete or real-time coverage of any news category.
- Chinese headline and summary translation requires internet access and uses a public machine-translation endpoint. If that service is unavailable or rate-limited, the row displays a translation-unavailable notice with the original text.
- Market cap can be missing for some symbols. The app has an `Allow missing market cap` option, but turning it on makes market-cap filters less strict.
- Mover ratio is approximated as latest daily volume divided by the previous 20-day average volume. It is not Futu's real-time volume ratio.
- Turnover is approximated as `Close * Volume`.
- The U.S. stock universe is filtered from NASDAQ Trader symbol files and excludes many ETFs, warrants, units, rights, preferreds, notes, and obvious non-common-stock instruments.

For more reliable production scanning, use a paid data provider with licensed historical daily OHLCV, market cap, and full-symbol coverage.
