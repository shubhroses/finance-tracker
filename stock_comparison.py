import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import argparse
from datetime import datetime, timedelta

def normalize_data(df):
    """Normalize data to start at 100 for easy percentage comparison"""
    return df / df.iloc[0] * 100

def fetch_and_compare_stocks(tickers, start_date, end_date, interval='1d'):
    """Fetch and compare stock data for the given tickers and time period"""
    print(f"Fetching data for: {', '.join(tickers)}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Interval: {interval}")
    
    # Create an empty DataFrame to store the closing prices
    all_data = pd.DataFrame()
    
    # Fetch data for each ticker
    for ticker in tickers:
        try:
            data = yf.download(ticker, start=start_date, end=end_date, 
                              interval=interval, progress=False, auto_adjust=True)
            if data.empty:
                print(f"No data found for {ticker}")
                continue
                
            all_data[ticker] = data['Close']
            print(f"✓ {ticker}: {len(data)} data points")
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
    
    # Check if we have data
    if all_data.empty:
        print("No data found for any of the tickers")
        return None
    
    # Calculate stats
    returns = all_data.pct_change().dropna()
    
    # Total return
    total_return = (all_data.iloc[-1] / all_data.iloc[0] - 1) * 100
    
    # Annualized volatility
    if interval == '1d':
        trading_days = 252
    elif interval == '1wk':
        trading_days = 52
    elif interval == '1mo':
        trading_days = 12
    else:
        trading_days = 252
        
    volatility = returns.std() * (trading_days ** 0.5) * 100
    
    # Sharpe ratio (assuming 2% risk-free rate)
    risk_free_rate = 0.02
    sharpe = (total_return / 100) / (volatility / 100)
    
    # Display results
    print("\nPerformance Metrics:")
    print(f"{'Ticker':<8} {'Total Return':<15} {'Annualized Vol':<15} {'Sharpe Ratio':<12}")
    print("-" * 50)
    
    for ticker in all_data.columns:
        print(f"{ticker:<8} {total_return[ticker]:>8.2f}% {volatility[ticker]:>14.2f}% {sharpe[ticker]:>12.2f}")
    
    # Normalize the data for comparison
    normalized_data = normalize_data(all_data)
    
    # Plot the data
    plt.figure(figsize=(12, 6))
    for ticker in normalized_data.columns:
        plt.plot(normalized_data.index, normalized_data[ticker], label=ticker)
    
    plt.title('Stock Performance Comparison (Normalized to 100)')
    plt.xlabel('Date')
    plt.ylabel('Normalized Price')
    plt.legend()
    plt.grid(True)
    
    # Add text with the performance stats
    y_pos = 0.02
    plt.figtext(0.02, y_pos, f"Period: {start_date} to {end_date}", fontsize=9)
    
    # Save the chart
    output_file = 'stock_comparison.png'
    plt.savefig(output_file)
    plt.close()
    
    print(f"\nComparison chart saved as '{output_file}'")
    
    return normalized_data

def parse_date(date_str):
    """Parse date string into datetime object"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a valid date: {date_str}. Format: YYYY-MM-DD")

def main():
    parser = argparse.ArgumentParser(description='Compare stock performance')
    parser.add_argument('tickers', type=str, nargs='+', help='Stock ticker symbols (e.g., AAPL MSFT GOOGL)')
    parser.add_argument('--start', type=parse_date, default=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                        help='Start date (YYYY-MM-DD), default: 1 year ago')
    parser.add_argument('--end', type=parse_date, default=datetime.now().strftime('%Y-%m-%d'),
                        help='End date (YYYY-MM-DD), default: today')
    parser.add_argument('--interval', type=str, choices=['1d', '1wk', '1mo'], default='1d',
                        help='Data interval: 1d (daily), 1wk (weekly), 1mo (monthly). Default: 1d')
    
    args = parser.parse_args()
    
    # Make sure all tickers are uppercase
    tickers = [ticker.upper() for ticker in args.tickers]
    
    fetch_and_compare_stocks(tickers, args.start, args.end, args.interval)

if __name__ == "__main__":
    main() 