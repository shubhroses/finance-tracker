# YFinance Demo

A simple demonstration of the `yfinance` library capabilities for retrieving and analyzing stock market data.

## Features Demonstrated

This repository contains three demo scripts showcasing different ways to use the yfinance library:

1. **yfinance_demo.py** - A basic demonstration of core yfinance features
2. **portfolio_analysis.py** - Analysis of a portfolio of stocks with performance metrics
3. **stock_comparison.py** - Command-line tool to compare multiple stocks over a specific time period

## Requirements

- Python 3.6+
- yfinance
- matplotlib
- pandas
- numpy (for portfolio analysis)

## Installation

Install the required packages:

```bash
pip install yfinance matplotlib pandas numpy
```

## Usage

### 1. Basic YFinance Demo

Run the basic demo script:

```bash
python yfinance_demo.py
```

This will:
- Fetch data for Apple Inc. (AAPL)
- Display company information
- Print recent historical price data
- Create a chart image (`stock_chart.png`)
- Show financial statement data
- Display dividend information

### 2. Portfolio Analysis

Run the portfolio analysis script:

```bash
python portfolio_analysis.py
```

This script:
- Analyzes a pre-defined portfolio (AAPL, MSFT, AMZN, GOOGL, TSLA)
- Calculates portfolio returns, volatility, and Sharpe ratio
- Creates a performance chart showing all stocks and the portfolio (`portfolio_performance.png`)
- Generates a correlation matrix heatmap of stock returns (`correlation_matrix.png`)

### 3. Stock Comparison Tool

Run the stock comparison tool with command-line arguments:

```bash
python stock_comparison.py AAPL MSFT GOOGL
```

Additional options:
```bash
python stock_comparison.py AAPL MSFT GOOGL --start 2023-01-01 --end 2024-01-01 --interval 1wk
```

Parameters:
- Positional arguments: Ticker symbols to compare
- `--start`: Start date (YYYY-MM-DD), defaults to 1 year ago
- `--end`: End date (YYYY-MM-DD), defaults to today
- `--interval`: Data interval (1d, 1wk, 1mo), defaults to 1d (daily)

The script will:
- Download price data for the specified stocks
- Calculate performance metrics (returns, volatility, Sharpe ratio)
- Create a comparison chart with normalized prices (`stock_comparison.png`)

## Customization

### Basic Demo
To analyze a different stock in the basic demo, change the `ticker_symbol` variable in the script:

```python
# Define the ticker symbol
ticker_symbol = "MSFT"  # Microsoft instead of Apple
```

### Portfolio Analysis
To modify the portfolio, edit the `portfolio` dictionary in the script:

```python
portfolio = {
    'AAPL': 0.20,   # Apple (20%)
    'MSFT': 0.20,   # Microsoft (20%)
    'AMZN': 0.20,   # Amazon (20%)
    'GOOGL': 0.20,  # Alphabet (20%)
    'BRK-B': 0.20   # Berkshire Hathaway (20%)
}
```

## Additional YFinance Features

The `yfinance` library offers many more features not covered in these demos:
- Options chain data
- Recommendation trends
- Institutional holders information
- News and analysis
- Balance sheet and cash flow statements

## Resources

- [YFinance Documentation](https://github.com/ranaroussi/yfinance)
- [Yahoo Finance](https://finance.yahoo.com/) 