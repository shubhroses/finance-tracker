# Finance Tracker

A Streamlit dashboard for looking at a single stock, comparing several tickers side by side, and analysing a set of holdings. Market data comes from Yahoo Finance through the [yfinance](https://github.com/ranaroussi/yfinance) library, and the charts are drawn with Plotly.

No API keys or configuration are needed.

The code dates from March 2025. It was last run on 8 October 2026: the server starts and all three modes run with their default inputs, but some figures are wrong and the news tab came back empty. See [Known issues](#known-issues).

## What it does

The sidebar switches between three modes.

### Stock Analysis

Enter a ticker (default `AAPL`) and choose a period (`1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y` or `max`; default `1y`). With the ticker box empty the page shows a short welcome text instead. Otherwise it shows five tabs, or an error message if the company lookup fails:

| Tab | Contents |
| --- | --- |
| Overview | Business summary, market cap, trailing P/E, 52-week high and low, volume, average volume, industry, sector, website |
| Charts | Candlestick price chart with a volume panel |
| Technical Analysis | Four sub-tabs, described below |
| Financials | Four sub-tabs. Key Metrics: market cap, revenue, gross profit, trailing and forward P/E, PEG, profit and operating margins, dividend yield. Income Statement, Balance Sheet and Cash Flow: a bar chart of selected line items by reporting date, with the full statement in an expander |
| News & Sentiment | Headlines with publisher, date and link, plus a summary when the source supplies one. No sentiment score is shown |

Technical Analysis sub-tabs. Checkboxes in the sidebar, all ticked by default, control the first three:

- **Moving Averages** ("Show Moving Averages"): simple moving averages of the close for any of 5, 10, 20, 50, 100 and 200 days (default 20, 50 and 200). When both 50 and 200 are selected, golden and death crosses are marked on the chart, with the date of the most recent of each and the price change since.
- **Oscillators** ("Show RSI", "Show MACD"): RSI (14) with lines at 70 and 30, and MACD (12, 26, 9) with signal line and histogram, each with a short reading.
- **Volatility** ("Show Bollinger Bands", "Show Volatility"): Bollinger Bands (20, 2) with current versus average band width; 20-day annualised historical volatility; ATR (14).
- **Support/Resistance** (always shown): pivot highs and lows, where a pivot is a bar whose high is above, or whose low is below, that of each of the 10 bars before and after it. Neighbouring pivot prices within 1% of each other are grouped, and each group of two or more is reported as a level at the group's average price. Levels within 15% of the last close are drawn on the chart, and up to three of the nearest levels on each side of the last close are listed.

RSI and ATR are computed with simple rolling means rather than Wilder's smoothing.

### Compare Stocks

Enter comma-separated tickers (default `AAPL, MSFT, GOOGL`) and a period (same choices, default `1y`). Four tabs:

- **Price Performance**: summary table (latest close, change over the period, period high and low, average volume), a price chart, a chart of percentage change since the start of the period, and a volume chart.
- **Financial Metrics**: a table of market cap, trailing and forward P/E, PEG, price/book, profit and operating margins, ROE, ROA, revenue growth and dividend yield, with bar charts for P/E, PEG, price/book, dividend yield and the four profitability ratios.
- **Technical Indicators**: for each ticker, price with 20- and 50-day moving averages, RSI (14) and MACD (12, 26, 9), with a one-line reading of each.
- **Correlation**: heatmap of daily-return correlations, and the three highest and three lowest pairs.

### Portfolio Analysis

Enter tickers, share counts and purchase dates (`YYYY-MM-DD`) as three comma-separated lists of the same length. The defaults are `AAPL, MSFT, GOOGL`, `10, 15, 5` and today's date for each holding. Five tabs:

- **Overview**: total value, total gain/loss, value-weighted beta and dividend yield, a holdings table, and a sector allocation chart.
- **Performance**: a chart of portfolio value over the past year with SPY rebased to 100, a chart of daily returns, and total return, annualised return, volatility, Sharpe ratio (2% risk-free rate assumed), maximum drawdown and beta against SPY.
- **Risk Analysis**: correlation heatmap and, per holding, beta as reported by Yahoo Finance, annualised volatility, one-day 95% historical value at risk, and maximum drawdown.
- **Allocation**: pie charts and tables of weights by stock and by sector.
- **Rebalancing**: a table of the trades needed to bring every holding to an equal weight, and a recommendation for each position more than five percentage points from that target.

Portfolio figures use one year of daily prices. The purchase price is the close on the purchase date when that date is a trading day within the last year. Otherwise the current price is used, which makes the gain/loss for that holding zero. With the default dates (today) the gain/loss is always zero.

## How data is fetched

`components/utils.py` wraps the calls behind the Overview, Charts, Financials and News tabs:

- Results are cached for five minutes with `st.cache_data`. A lookup that failed and returned nothing is cached as well.
- A limiter shared by the whole server process keeps at least two seconds between the start of one uncached call and the next.
- Company info and news lookups make up to five attempts when the result is empty or the error message contains `429`, waiting about 4, 8, 16 and 32 seconds between attempts plus up to half a second of random jitter. Any other error ends the lookup at once. Price history and financial statements are requested once.
- Page scraping goes through a shared `requests.Session` that retries GET requests up to five times on 429, 500, 502, 503 and 504 responses. The helpers also assign this session to a `_session` attribute on the `yfinance` ticker object. yfinance 1.7.0 does not read that attribute, so its own requests are unaffected.

News is looked up in this order: `yfinance`; then a scrape of the ticker's news page on Yahoo Finance; then, if there is still nothing usable, a scrape of the ticker's page on MarketWatch.

The Technical Analysis tab and the Compare Stocks and Portfolio Analysis modes call `yfinance` directly, without the cache or the limiter.

## Run locally

```bash
git clone https://github.com/shubhroses/finance-tracker.git
cd finance-tracker
python3 -m venv venv            # Windows: python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints the local URL when it starts (http://localhost:8501 by default).

`requirements.txt` sets minimum versions only, so `pip` installs the newest releases that support the interpreter. The minimums need Python 3.9 or newer. The run on 8 October 2026 was on macOS (Apple silicon) with these versions:

| Python | streamlit | yfinance | pandas | numpy | plotly |
| --- | --- | --- | --- | --- | --- |
| 3.10.18 | 1.65.0 | 1.7.0 | 2.3.3 | 2.2.6 | 7.1.0 |
| 3.13.7 | 1.65.0 | 1.7.0 | 3.0.6 | 2.5.3 | 7.1.0 |
| 3.14.6 | 1.65.0 | 1.7.0 | 3.0.6 | 2.5.3 | 7.1.0 |

On Python 3.14 `pip` had to build `watchdog` from source because there was no wheel for it.

With these versions Streamlit logs a deprecation warning for `use_container_width`, which every `st.plotly_chart` call in the components passes.

Of the packages in `requirements.txt`, the code imports `streamlit`, `yfinance`, `pandas`, `numpy`, `plotly`, `beautifulsoup4` and `requests`. No module imports `scikit-learn`, `lxml`, `html5lib`, `python-dateutil`, `pytz`, `tenacity` or `watchdog` (Streamlit uses `watchdog` itself when it is installed).

## Deploying

The app reads no secrets or environment variables. A host only has to install `requirements.txt` and run `app.py` with Streamlit. For Streamlit Community Cloud, follow [Deploy your app on Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) with a fork of this repository. Deployment was not tried while writing this README.

## Project structure

```
finance-tracker/
├── app.py                 # Page config, custom CSS, routing between the three modes
├── requirements.txt
├── LICENSE
├── components/
│   ├── __init__.py
│   ├── sidebar.py         # Mode, ticker, period and indicator controls
│   ├── overview.py        # Overview tab
│   ├── charts.py          # Candlestick and volume chart
│   ├── technical.py       # Moving averages, RSI, MACD, Bollinger Bands, volatility, ATR, support/resistance
│   ├── financials.py      # Key metrics and financial statements
│   ├── news.py            # News tab and the MarketWatch scrape
│   ├── comparison.py      # Compare Stocks mode
│   ├── portfolio.py       # Portfolio Analysis mode
│   └── utils.py           # Cached, rate-limited yfinance helpers and the shared requests session
└── utils/
    ├── __init__.py
    ├── config.py          # Not imported by the app
    └── version_check.py   # Not imported by the app
```

Code that is present but never called:

- `components/news.py`: a keyword-based sentiment scorer and its charts (`analyze_article_sentiment`, `show_sentiment_analysis`), a view of news against price (`show_news_impact`), a second headline list (`show_recent_news`), and scrapers for Yahoo Finance and Seeking Alpha (`get_yahoo_finance_news`, `get_seeking_alpha_news`).
- `components/charts.py`: `highlight_significant_price_changes`.
- The `utils/` package. `utils/version_check.py` imports `pkg_resources`, which `requirements.txt` does not install; the import failed in the Python 3.13 environment above.

## Known issues

Found on 8 October 2026 by running the script through Streamlit's `AppTest` harness on Python 3.13 with the versions above, using the default inputs unless stated. The news, dividend yield and portfolio results were the same on Python 3.10 and 3.14. The pages were not inspected in a browser.

- **The news tab came back empty.** `yfinance` returned no news items (Yahoo answered its request with HTTP 404), the Yahoo Finance page scrape matched no elements, and MarketWatch answered HTTP 401. The tab showed its "No news articles could be retrieved" warning. The retry waits described above made the first run for a ticker take about 75 seconds.
- **Dividend yield is shown 100 times too large.** `yfinance` reported `dividendYield` already as a percentage (0.32 for AAPL). The Financials tab, the Compare Stocks table and the portfolio holdings table multiply it by 100 again and showed 32.00%. The portfolio-level "Dividend Yield" figure does not rescale it and is unaffected.
- **"Show RSI" off with "Show MACD" on breaks the Technical Analysis tab.** The MACD chart is drawn, then an error about the variable `col2` is shown, and the Volatility and Support/Resistance sub-tabs stay empty.
- **"Show Max Drawdown" does nothing.** The checkbox value is passed to the Technical Analysis tab, and no code reads it.
- **Portfolio Performance figures are not usable.** The portfolio value series is built on a calendar-day index and is zero on every day without trading (114 of 365 days in the run). The value chart drops to zero on those days, and the tab showed `nan` for volatility, Sharpe ratio and beta and -100.00% for maximum drawdown. When the current day has no price bar, the series also ends at zero and total and annualised return show -100.00% (reproduced by dropping the latest bar). SPY is rebased to 100 but drawn on the same dollar axis as the portfolio value.
- **Portfolio weights are wrong in two tables.** The "Weight" column of the Overview holdings table and of the Allocation stock table is computed against a running total as holdings are loaded, so the first holding always shows 100% (the run showed 100.0%, 69.7% and 13.4%). The pie charts, the sector table and the Rebalancing tab use the full total.
- **Statement charts can miss rows.** The bar charts look up fixed row names and skip any that the statement does not contain. For AAPL the balance sheet chart showed two of its five items and the cash flow chart four of five.

## Limitations

- `yfinance` is not affiliated with or endorsed by Yahoo. Requests can be rate-limited or fail when Yahoo changes its site, and the scrapers depend on page markup that changes without notice.
- Holdings are typed in each session; nothing is saved.
- There are no automated tests.
- The readings shown next to indicators ("bullish", "overbought" and so on) are the textbook interpretations of those indicators. Nothing in the app is investment advice.

## License

[MIT](LICENSE)
