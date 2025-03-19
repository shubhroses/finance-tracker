import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import plotly.express as px

def show_portfolio_analyzer():
    """Display portfolio analysis tools."""
    
    st.header('Portfolio Analysis')
    
    # Portfolio input section
    st.subheader('Portfolio Composition')
    
    # Add instructions
    with st.expander("How to Use Portfolio Analyzer", expanded=True):
        st.write("""
        1. Enter your stock holdings in the form below
        2. For each stock, provide:
           - Ticker symbol (e.g., AAPL)
           - Number of shares
           - Purchase date (YYYY-MM-DD)
        3. View analysis in the tabs below
        """)
    
    # Create a dynamic form for portfolio input
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        default_tickers = "AAPL, MSFT, GOOGL"
        tickers_input = st.text_input(
            'Stock Tickers (comma-separated)',
            default_tickers,
            help="Enter stock ticker symbols separated by commas"
        )
    
    with col2:
        default_shares = "10, 15, 5"
        shares_input = st.text_input(
            'Number of Shares',
            default_shares,
            help="Enter number of shares for each stock"
        )
    
    with col3:
        default_date = datetime.now().strftime('%Y-%m-%d')
        dates_input = st.text_input(
            'Purchase Dates',
            f"{default_date}, {default_date}, {default_date}",
            help="Enter purchase dates in YYYY-MM-DD format"
        )
    
    try:
        # Parse inputs
        tickers = [ticker.strip().upper() for ticker in tickers_input.split(',')]
        shares = [float(shares.strip()) for shares in shares_input.split(',')]
        dates = [date.strip() for date in dates_input.split(',')]
        
        if len(tickers) == len(shares) == len(dates):
            # Show loading message
            with st.spinner('Analyzing portfolio...'):
                # Get stock data and calculate portfolio metrics
                portfolio_data = get_portfolio_data(tickers, shares, dates)
                
                if portfolio_data:
                    # Create tabs for different analyses
                    portfolio_tabs = st.tabs([
                        '📊 Overview',
                        '📈 Performance',
                        '⚠️ Risk Analysis',
                        '🎯 Allocation',
                        '🔄 Rebalancing'
                    ])
                    
                    with portfolio_tabs[0]:
                        show_portfolio_summary(portfolio_data)
                    
                    with portfolio_tabs[1]:
                        show_portfolio_performance(portfolio_data)
                    
                    with portfolio_tabs[2]:
                        show_portfolio_risk_analysis(portfolio_data)
                    
                    with portfolio_tabs[3]:
                        show_portfolio_allocation(portfolio_data)
                    
                    with portfolio_tabs[4]:
                        show_rebalancing_suggestions(portfolio_data)
        else:
            st.error("Number of tickers, shares, and dates must match. Please check your input.")
            st.info("""
            **Example Input Format:**
            - Tickers: AAPL, MSFT, GOOGL
            - Shares: 10, 15, 5
            - Dates: 2023-01-01, 2023-01-01, 2023-01-01
            """)
    
    except ValueError as ve:
        st.error(f"Invalid input format: {str(ve)}")
        st.info("Please ensure all numbers and dates are in the correct format")
    except Exception as e:
        st.error(f"Error in portfolio analysis: {str(e)}")
        st.info("Please check your inputs and try again")


def get_portfolio_data(tickers, shares, dates):
    """Fetch and calculate portfolio data."""
    
    portfolio_data = []
    total_value = 0
    
    for ticker, share_count, purchase_date in zip(tickers, shares, dates):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period='1y')
            
            if not hist.empty and info:
                current_price = hist['Close'].iloc[-1]
                purchase_price = hist.loc[purchase_date:].iloc[0]['Close'] if purchase_date in hist.index else current_price
                market_value = current_price * share_count
                cost_basis = purchase_price * share_count
                gain_loss = market_value - cost_basis
                gain_loss_pct = (gain_loss / cost_basis) * 100 if cost_basis != 0 else 0
                
                total_value += market_value
                
                portfolio_data.append({
                    'Ticker': ticker,
                    'Shares': share_count,
                    'Purchase Date': purchase_date,
                    'Purchase Price': purchase_price,
                    'Current Price': current_price,
                    'Market Value': market_value,
                    'Cost Basis': cost_basis,
                    'Gain/Loss': gain_loss,
                    'Gain/Loss %': gain_loss_pct,
                    'Historical Data': hist,
                    'Company Name': info.get('longName', ticker),
                    'Sector': info.get('sector', 'Unknown'),
                    'Beta': info.get('beta', 1.0),
                    'Dividend Yield': info.get('dividendYield', 0),
                    'Weight': (market_value / total_value) * 100 if total_value > 0 else 0
                })
        
        except Exception as e:
            st.warning(f"Could not fetch data for {ticker}: {str(e)}")
    
    return portfolio_data


def show_portfolio_summary(portfolio_data):
    """Display portfolio summary metrics."""
    
    st.subheader('Portfolio Overview')
    
    # Calculate portfolio metrics
    total_market_value = sum(stock['Market Value'] for stock in portfolio_data)
    total_cost_basis = sum(stock['Cost Basis'] for stock in portfolio_data)
    total_gain_loss = sum(stock['Gain/Loss'] for stock in portfolio_data)
    total_gain_loss_pct = (total_gain_loss / total_cost_basis) * 100 if total_cost_basis != 0 else 0
    
    # Display key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Value",
            f"${total_market_value:,.2f}",
            help="Current total portfolio value"
        )
    
    with col2:
        st.metric(
            "Total Gain/Loss",
            f"${total_gain_loss:,.2f}",
            f"{total_gain_loss_pct:+.2f}%",
            delta_color="normal" if total_gain_loss >= 0 else "inverse"
        )
    
    with col3:
        # Calculate weighted average beta
        weighted_beta = sum(stock['Beta'] * stock['Market Value'] for stock in portfolio_data) / total_market_value
        st.metric(
            "Portfolio Beta",
            f"{weighted_beta:.2f}",
            help="Weighted average beta (market risk)"
        )
    
    with col4:
        # Calculate weighted average dividend yield
        weighted_div_yield = sum(stock['Dividend Yield'] * stock['Market Value'] for stock in portfolio_data) / total_market_value
        st.metric(
            "Dividend Yield",
            f"{weighted_div_yield:.2f}%",
            help="Weighted average dividend yield"
        )
    
    # Create summary table
    st.write("**Holdings Summary**")
    
    summary_data = []
    for stock in portfolio_data:
        summary_data.append({
            'Ticker': stock['Ticker'],
            'Company': stock['Company Name'],
            'Sector': stock['Sector'],
            'Shares': f"{stock['Shares']:,.0f}",
            'Current Price': f"${stock['Current Price']:.2f}",
            'Market Value': f"${stock['Market Value']:,.2f}",
            'Weight': f"{stock['Weight']:.1f}%",
            'Gain/Loss': f"${stock['Gain/Loss']:,.2f}",
            'Gain/Loss %': f"{stock['Gain/Loss %']:+.1f}%",
            'Beta': f"{stock['Beta']:.2f}",
            'Div Yield': f"{stock['Dividend Yield']*100:.2f}%" if stock['Dividend Yield'] else 'N/A'
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(
        summary_df.set_index('Ticker'),
        use_container_width=True,
        hide_index=False
    )
    
    # Add sector allocation chart
    st.subheader('Sector Allocation')
    
    sector_data = {}
    for stock in portfolio_data:
        sector = stock['Sector']
        if sector in sector_data:
            sector_data[sector] += stock['Market Value']
        else:
            sector_data[sector] = stock['Market Value']
    
    fig = go.Figure(data=[
        go.Pie(
            labels=list(sector_data.keys()),
            values=list(sector_data.values()),
            hole=0.4,
            textinfo='label+percent',
            marker=dict(colors=px.colors.qualitative.Set3)
        )
    ])
    
    fig.update_layout(
        title='Portfolio Sector Distribution',
        template='plotly_dark',
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_portfolio_performance(portfolio_data):
    """Display portfolio performance analysis."""
    
    st.subheader('Portfolio Performance')
    
    # Calculate portfolio value over time
    start_date = min(stock['Historical Data'].index.min() for stock in portfolio_data)
    end_date = pd.Timestamp.now()
    
    # Convert dates to timezone-naive format
    start_date = start_date.tz_localize(None)
    end_date = end_date.tz_localize(None)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    portfolio_values = pd.Series(0.0, index=dates)
    benchmark_values = pd.Series(0.0, index=dates)
    
    # Get SPY data for benchmark comparison
    try:
        spy = yf.Ticker('SPY')
        spy_hist = spy.history(period='1y')
        if not spy_hist.empty:
            # Convert index to timezone-naive
            spy_hist.index = spy_hist.index.tz_localize(None)
            benchmark_values = spy_hist['Close'] / spy_hist['Close'].iloc[0] * 100
    except:
        st.warning("Could not fetch benchmark (SPY) data")
    
    # Calculate portfolio value over time
    for stock in portfolio_data:
        hist_data = stock['Historical Data'].copy()
        # Convert index to timezone-naive
        hist_data.index = hist_data.index.tz_localize(None)
        shares = stock['Shares']
        portfolio_values = portfolio_values.add(hist_data['Close'] * shares, fill_value=0)
    
    # Calculate portfolio returns
    portfolio_returns = portfolio_values.pct_change()
    
    # Create performance visualization
    fig = make_subplots(rows=2, cols=1,
                        subplot_titles=('Portfolio Value Over Time', 'Daily Returns'),
                        vertical_spacing=0.15)
    
    # Portfolio value
    fig.add_trace(
        go.Scatter(
            x=portfolio_values.index,
            y=portfolio_values,
            name='Portfolio Value',
            line=dict(color='blue')
        ),
        row=1, col=1
    )
    
    # Benchmark comparison
    if not benchmark_values.empty:
        fig.add_trace(
            go.Scatter(
                x=benchmark_values.index,
                y=benchmark_values,
                name='S&P 500 (Normalized)',
                line=dict(color='gray', dash='dash')
            ),
            row=1, col=1
        )
    
    # Daily returns
    fig.add_trace(
        go.Bar(
            x=portfolio_returns.index,
            y=portfolio_returns * 100,
            name='Daily Returns (%)',
            marker_color='lightblue'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=800,
        template='plotly_dark',
        showlegend=True
    )
    
    fig.update_yaxes(title_text="Value ($)", row=1, col=1)
    fig.update_yaxes(title_text="Return (%)", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate and display performance metrics
    st.write("**Performance Metrics**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Calculate annualized return
        total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0] - 1) * 100
        days = (portfolio_values.index[-1] - portfolio_values.index[0]).days
        annualized_return = ((1 + total_return/100) ** (365/days) - 1) * 100
        
        st.write(f"Total Return: {total_return:.2f}%")
        st.write(f"Annualized Return: {annualized_return:.2f}%")
        st.write(f"Daily Volatility: {portfolio_returns.std() * 100:.2f}%")
        st.write(f"Annualized Volatility: {portfolio_returns.std() * np.sqrt(252) * 100:.2f}%")
    
    with col2:
        # Calculate Sharpe Ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        excess_returns = portfolio_returns - risk_free_rate/252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / portfolio_returns.std()
        
        # Calculate maximum drawdown
        rolling_max = portfolio_values.expanding().max()
        drawdowns = (portfolio_values - rolling_max) / rolling_max
        max_drawdown = drawdowns.min() * 100
        
        st.write(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        st.write(f"Maximum Drawdown: {max_drawdown:.2f}%")
        
        # Calculate beta if benchmark data is available
        if not benchmark_values.empty:
            benchmark_returns = benchmark_values.pct_change()
            covariance = portfolio_returns.cov(benchmark_returns)
            variance = benchmark_returns.var()
            portfolio_beta = covariance / variance
            st.write(f"Portfolio Beta: {portfolio_beta:.2f}")


def show_portfolio_risk_analysis(portfolio_data):
    """Display portfolio risk analysis."""
    
    st.subheader('Risk Analysis')
    
    # Calculate correlation matrix
    returns_data = {}
    for stock in portfolio_data:
        returns_data[stock['Ticker']] = stock['Historical Data']['Close'].pct_change()
    
    returns_df = pd.DataFrame(returns_data)
    correlation = returns_df.corr()
    
    # Create correlation heatmap
    fig = go.Figure(data=go.Heatmap(
        z=correlation,
        x=correlation.columns,
        y=correlation.columns,
        colorscale='RdBu',
        zmin=-1,
        zmax=1,
        text=correlation.round(2),
        texttemplate='%{text}',
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title='Stock Correlation Matrix',
        template='plotly_dark',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate and display risk metrics
    st.write("**Risk Metrics by Stock**")
    
    risk_data = []
    for stock in portfolio_data:
        returns = stock['Historical Data']['Close'].pct_change()
        beta = stock['Beta']
        volatility = returns.std() * np.sqrt(252) * 100  # Annualized volatility
        
        risk_data.append({
            'Ticker': stock['Ticker'],
            'Beta': f"{beta:.2f}",
            'Volatility (Annual)': f"{volatility:.2f}%",
            'Value at Risk (95%)': f"${stock['Market Value'] * returns.quantile(0.05):,.2f}",
            'Maximum Drawdown': f"{calculate_max_drawdown(stock['Historical Data']['Close']):.2f}%"
        })
    
    risk_df = pd.DataFrame(risk_data)
    st.dataframe(risk_df.set_index('Ticker'))


def show_portfolio_allocation(portfolio_data):
    """Display portfolio allocation analysis."""
    
    st.subheader('Portfolio Allocation')
    
    total_value = sum(stock['Market Value'] for stock in portfolio_data)
    
    # Create sector allocation chart
    sector_data = {}
    for stock in portfolio_data:
        sector = stock['Sector']
        value = stock['Market Value']
        sector_data[sector] = sector_data.get(sector, 0) + value
    
    # Create allocation charts
    fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])
    
    # Stock allocation
    stock_values = [stock['Market Value'] for stock in portfolio_data]
    stock_labels = [f"{stock['Ticker']} ({stock['Market Value']/total_value*100:.1f}%)"
                   for stock in portfolio_data]
    
    fig.add_trace(go.Pie(
        values=stock_values,
        labels=stock_labels,
        name="Stocks",
        title="Stock Allocation"
    ), 1, 1)
    
    # Sector allocation
    sector_values = list(sector_data.values())
    sector_labels = [f"{sector} ({value/total_value*100:.1f}%)"
                    for sector, value in sector_data.items()]
    
    fig.add_trace(go.Pie(
        values=sector_values,
        labels=sector_labels,
        name="Sectors",
        title="Sector Allocation"
    ), 1, 2)
    
    fig.update_layout(
        height=500,
        template='plotly_dark'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display allocation tables
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Stock Allocation**")
        stock_allocation = pd.DataFrame([
            {
                'Stock': stock['Ticker'],
                'Value': f"${stock['Market Value']:,.2f}",
                'Weight': f"{stock['Weight']:.2f}%"
            }
            for stock in portfolio_data
        ])
        st.dataframe(stock_allocation.set_index('Stock'))
    
    with col2:
        st.write("**Sector Allocation**")
        sector_allocation = pd.DataFrame([
            {
                'Sector': sector,
                'Value': f"${value:,.2f}",
                'Weight': f"{value/total_value*100:.2f}%"
            }
            for sector, value in sector_data.items()
        ])
        st.dataframe(sector_allocation.set_index('Sector'))


def show_rebalancing_suggestions(portfolio_data):
    """Display portfolio rebalancing suggestions."""
    
    st.subheader('Rebalancing Suggestions')
    
    total_value = sum(stock['Market Value'] for stock in portfolio_data)
    
    # Calculate current weights
    for stock in portfolio_data:
        stock['Weight'] = stock['Market Value'] / total_value
    
    # Define target weights (equal weight as default)
    target_weight = 1.0 / len(portfolio_data)
    
    # Calculate rebalancing needs
    rebalancing_data = []
    for stock in portfolio_data:
        current_weight = stock['Weight']
        weight_diff = target_weight - current_weight
        value_diff = weight_diff * total_value
        shares_diff = value_diff / stock['Current Price']
        
        rebalancing_data.append({
            'Ticker': stock['Ticker'],
            'Current Weight': f"{current_weight*100:.2f}%",
            'Target Weight': f"{target_weight*100:.2f}%",
            'Weight Difference': f"{weight_diff*100:+.2f}%",
            'Value Difference': f"${value_diff:,.2f}",
            'Shares to Trade': f"{shares_diff:+.2f}"
        })
    
    rebalancing_df = pd.DataFrame(rebalancing_data)
    st.dataframe(rebalancing_df.set_index('Ticker'))
    
    # Add rebalancing recommendations
    st.write("**Rebalancing Recommendations:**")
    
    for stock in portfolio_data:
        weight_diff = (target_weight - stock['Weight']) * 100
        if abs(weight_diff) > 5:  # Only show significant differences
            if weight_diff > 0:
                st.write(f"🔼 Increase {stock['Ticker']} position by {abs(weight_diff):.1f}%")
            else:
                st.write(f"🔽 Decrease {stock['Ticker']} position by {abs(weight_diff):.1f}%")


def calculate_max_drawdown(prices):
    """Calculate maximum drawdown percentage."""
    
    rolling_max = prices.expanding().max()
    drawdowns = (prices - rolling_max) / rolling_max
    return drawdowns.min() * 100 