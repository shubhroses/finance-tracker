import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def main():
    print("YFinance Portfolio Analysis Demo")
    print("================================")
    
    # Define a portfolio of ticker symbols and their weights
    portfolio = {
        'AAPL': 0.25,   # Apple
        'MSFT': 0.25,   # Microsoft
        'AMZN': 0.20,   # Amazon
        'GOOGL': 0.15,  # Alphabet (Google)
        'TSLA': 0.15    # Tesla
    }
    
    # Time period for analysis
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year of data
    
    print(f"Analyzing portfolio from {start_date.date()} to {end_date.date()}")
    print("\nPortfolio Composition:")
    for ticker, weight in portfolio.items():
        print(f"  {ticker}: {weight*100:.1f}%")
    
    # Download historical data for all tickers
    tickers_data = {}
    combined_data = pd.DataFrame()
    
    print("\nDownloading historical data...")
    for ticker in portfolio.keys():
        print(f"  Fetching data for {ticker}")
        stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
        tickers_data[ticker] = stock_data
        
        # Add this stock's close price to the combined dataframe
        combined_data[ticker] = stock_data['Close']
    
    # Calculate daily returns
    daily_returns = combined_data.pct_change().dropna()
    
    # Calculate portfolio return based on weights
    portfolio_returns = pd.Series(0, index=daily_returns.index)
    for ticker, weight in portfolio.items():
        portfolio_returns += daily_returns[ticker] * weight
    
    # Calculate cumulative returns
    cumulative_returns = (1 + daily_returns).cumprod() - 1
    portfolio_cumulative_returns = (1 + portfolio_returns).cumprod() - 1
    
    # Print performance metrics
    print("\nPerformance Metrics:")
    print(f"  Portfolio Annual Return: {portfolio_cumulative_returns.iloc[-1]*100:.2f}%")
    
    # Calculate annualized volatility (standard deviation of returns * sqrt(trading days in a year))
    volatility = portfolio_returns.std() * np.sqrt(252)
    print(f"  Portfolio Volatility (Annualized): {volatility*100:.2f}%")
    
    # Calculate Sharpe Ratio (assuming risk-free rate of 2%)
    risk_free_rate = 0.02
    sharpe_ratio = (portfolio_cumulative_returns.iloc[-1] - risk_free_rate) / volatility
    print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
    
    # Plot the cumulative returns for each stock and the portfolio
    plt.figure(figsize=(12, 8))
    
    # Plot individual stocks
    for ticker in portfolio.keys():
        plt.plot(cumulative_returns.index, cumulative_returns[ticker] * 100, alpha=0.7, label=ticker)
    
    # Plot portfolio
    plt.plot(portfolio_cumulative_returns.index, portfolio_cumulative_returns * 100, 
             linewidth=3, color='black', label='Portfolio')
    
    plt.title('Cumulative Returns (%)')
    plt.xlabel('Date')
    plt.ylabel('Return (%)')
    plt.legend()
    plt.grid(True)
    plt.savefig('portfolio_performance.png')
    plt.close()
    print("\nPortfolio performance chart saved as 'portfolio_performance.png'")
    
    # Create a correlation matrix heat map
    plt.figure(figsize=(10, 8))
    correlation_matrix = daily_returns.corr()
    plt.imshow(correlation_matrix, cmap='coolwarm', vmin=-1, vmax=1)
    
    # Add text annotations
    for i in range(len(correlation_matrix.columns)):
        for j in range(len(correlation_matrix.columns)):
            plt.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                     ha='center', va='center', color='white' if abs(correlation_matrix.iloc[i, j]) > 0.5 else 'black')
    
    plt.colorbar(label='Correlation Coefficient')
    plt.xticks(range(len(correlation_matrix.columns)), correlation_matrix.columns, rotation=45)
    plt.yticks(range(len(correlation_matrix.columns)), correlation_matrix.columns)
    plt.title('Correlation Matrix of Stock Returns')
    plt.tight_layout()
    plt.savefig('correlation_matrix.png')
    plt.close()
    print("Correlation matrix saved as 'correlation_matrix.png'")

if __name__ == "__main__":
    main()