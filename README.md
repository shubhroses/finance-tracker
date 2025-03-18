# YFinance Demo

A simple demonstration of the `yfinance` library capabilities for retrieving and analyzing stock market data.

## Features Demonstrated

This demo showcases:

1. **Basic Company Information** - Retrieving key data points about a company
2. **Historical Data** - Downloading stock price history for a specified time period
3. **Data Visualization** - Creating a simple price chart
4. **Financial Statements** - Accessing income statement data
5. **Dividend Information** - Retrieving dividend history and yield

## Requirements

- Python 3.6+
- yfinance
- matplotlib
- pandas

## Installation

Install the required packages:

```bash
pip install yfinance matplotlib pandas
```

## Usage

Run the demo script:

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

## Customization

To analyze a different stock, change the `ticker_symbol` variable in the script:

```python
# Define the ticker symbol
ticker_symbol = "MSFT"  # Microsoft instead of Apple
```

## Additional YFinance Features

The `yfinance` library offers many more features not covered in this demo:

- Options chain data
- Recommendation trends
- Institutional holders information
- News and analysis
- Balance sheet and cash flow statements

## Resources

- [YFinance Documentation](https://github.com/ranaroussi/yfinance)
- [Yahoo Finance](https://finance.yahoo.com/) 