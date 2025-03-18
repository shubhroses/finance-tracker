import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

def main():
    print("Simple YFinance Demo")
    print("====================")
    
    # Define the ticker symbol
    ticker_symbol = "AAPL"
    
    # Create a Ticker object
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. Basic info
    print(f"\n1. Basic Information for {ticker_symbol}:")
    info = ticker.info
    print(f"Company Name: {info.get('longName', 'N/A')}")
    print(f"Industry: {info.get('industry', 'N/A')}")
    print(f"Current Price: ${info.get('currentPrice', 'N/A')}")
    print(f"Market Cap: ${info.get('marketCap', 'N/A')}")
    print(f"52 Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}")
    print(f"52 Week Low: ${info.get('fiftyTwoWeekLow', 'N/A')}")
    
    # 2. Historical data (last 1 year)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print(f"\n2. Downloading historical data from {start_date.date()} to {end_date.date()}")
    hist = ticker.history(start=start_date, end=end_date)
    
    print(f"Downloaded {len(hist)} days of data")
    print("\nLast 5 days:")
    print(hist.tail())
    
    # 3. Plot closing price
    print("\n3. Plotting closing price chart (saved as 'stock_chart.png')")
    plt.figure(figsize=(12, 6))
    plt.plot(hist.index, hist['Close'])
    plt.title(f"{info.get('longName', ticker_symbol)} Stock Price - Last Year")
    plt.xlabel('Date')
    plt.ylabel('Stock Price ($)')
    plt.grid(True)
    plt.savefig('stock_chart.png')
    plt.close()
    
    # 4. Financial data
    print("\n4. Financial Data (Income Statement - Last Fiscal Year)")
    try:
        income_stmt = ticker.income_stmt
        if not income_stmt.empty:
            recent_year = income_stmt.columns[0]
            print(f"Fiscal Year: {recent_year}")
            
            # Display key metrics
            metrics = ['Total Revenue', 'Gross Profit', 'Net Income']
            for metric in metrics:
                if metric in income_stmt.index:
                    value = income_stmt.loc[metric, recent_year]
                    print(f"{metric}: ${value:,.2f}")
        else:
            print("Income statement data not available")
    except Exception as e:
        print(f"Could not retrieve income statement: {e}")
    
    # 5. Dividends
    print("\n5. Dividend Information")
    try:
        dividends = ticker.dividends
        if len(dividends) > 0:
            # Use iloc to access by position rather than by index
            last_dividend = dividends.iloc[-1]
            last_dividend_date = dividends.index[-1].date()
            print(f"Latest dividend: ${last_dividend:.2f} (Date: {last_dividend_date})")
            print(f"Annual dividend yield: {info.get('dividendYield', 'N/A')}")
        else:
            print(f"{ticker_symbol} does not pay dividends")
    except Exception as e:
        print(f"Could not retrieve dividend information: {e}")

if __name__ == "__main__":
    main() 