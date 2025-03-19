import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def show_stock_comparison():
    """Display stock comparison analysis."""
    
    st.header('Stock Comparison')
    
    # Create columns for input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Get user input for stocks to compare
        st.write("Enter stock tickers separated by commas (e.g., AAPL, MSFT, GOOGL)")
        tickers_input = st.text_input('Stock Tickers', 'AAPL, MSFT, GOOGL')
    
    with col2:
        # Get time period for comparison
        period = st.selectbox(
            'Select Time Period',
            ['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'],
            index=3
        )
    
    if tickers_input:
        # Parse and clean tickers
        tickers = [ticker.strip().upper() for ticker in tickers_input.split(',')]
        
        # Show loading message
        with st.spinner('Fetching data for comparison...'):
            # Create tabs for different comparisons
            comp_tabs = st.tabs([
                '📈 Price Performance',
                '💰 Financial Metrics',
                '📊 Technical Indicators',
                '🔄 Correlation'
            ])
            
            with comp_tabs[0]:
                show_price_comparison(tickers, period)
            
            with comp_tabs[1]:
                show_financial_comparison(tickers)
            
            with comp_tabs[2]:
                show_technical_comparison(tickers, period)
            
            with comp_tabs[3]:
                show_correlation_analysis(tickers, period)
    else:
        # Show instructions if no tickers entered
        st.info("""
        ### How to Compare Stocks
        1. Enter two or more stock ticker symbols in the input field above
        2. Separate the tickers with commas (e.g., AAPL, MSFT, GOOGL)
        3. Select a time period for the comparison
        4. View different analyses in the tabs below
        
        ### Available Comparisons
        - **Price Performance**: Compare stock price movements and returns
        - **Financial Metrics**: Compare key financial ratios and metrics
        - **Technical Indicators**: Compare technical analysis indicators
        - **Correlation**: Analyze how the stocks move in relation to each other
        """)

def show_price_comparison(tickers, period):
    """Display price performance comparison."""
    
    st.subheader('Price Performance Comparison')
    
    try:
        # Get historical data for all tickers
        data = {}
        normalized_data = {}
        start_prices = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                if not hist.empty:
                    data[ticker] = hist
                    # Normalize prices to compare percentage changes
                    start_price = hist['Close'].iloc[0]
                    start_prices[ticker] = start_price
                    normalized_data[ticker] = (hist['Close'] / start_price - 1) * 100
            except Exception as e:
                st.warning(f"Could not fetch data for {ticker}: {e}")
        
        if data:
            # Display summary statistics first
            st.write("**Performance Summary**")
            
            summary_data = []
            for ticker in data.keys():
                hist = data[ticker]
                current_price = hist['Close'].iloc[-1]
                start_price = hist['Close'].iloc[0]
                change_pct = ((current_price - start_price) / start_price) * 100
                high = hist['High'].max()
                low = hist['Low'].min()
                
                summary_data.append({
                    'Ticker': ticker,
                    'Current Price': f"${current_price:.2f}",
                    'Change (%)': f"{change_pct:.1f}%",
                    'Period High': f"${high:.2f}",
                    'Period Low': f"${low:.2f}",
                    'Volume (Avg)': f"{hist['Volume'].mean():,.0f}"
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(
                summary_df.set_index('Ticker'),
                use_container_width=True,
                hide_index=False
            )
            
            # Create price comparison charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Absolute price chart
                fig = go.Figure()
                for ticker in data.keys():
                    fig.add_trace(
                        go.Scatter(
                            x=data[ticker].index,
                            y=data[ticker]['Close'],
                            name=f"{ticker} (${data[ticker]['Close'].iloc[-1]:.2f})",
                            mode='lines'
                        )
                    )
                
                fig.update_layout(
                    title='Stock Price Comparison',
                    yaxis_title='Price ($)',
                    template='plotly_dark',
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Normalized comparison chart
                fig_norm = go.Figure()
                for ticker, norm_prices in normalized_data.items():
                    fig_norm.add_trace(
                        go.Scatter(
                            x=norm_prices.index,
                            y=norm_prices,
                            name=f"{ticker} ({norm_prices.iloc[-1]:.1f}%)",
                            mode='lines'
                        )
                    )
                
                fig_norm.update_layout(
                    title='Normalized Price Performance (%)',
                    yaxis_title='Change (%)',
                    template='plotly_dark',
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_norm, use_container_width=True)
            
            # Add volume comparison
            st.subheader('Volume Analysis')
            fig_vol = go.Figure()
            
            for ticker in data.keys():
                fig_vol.add_trace(
                    go.Bar(
                        x=data[ticker].index,
                        y=data[ticker]['Volume'],
                        name=ticker,
                        opacity=0.7
                    )
                )
            
            fig_vol.update_layout(
                title='Trading Volume Comparison',
                yaxis_title='Volume',
                template='plotly_dark',
                height=300,
                hovermode='x unified',
                barmode='group'
            )
            
            st.plotly_chart(fig_vol, use_container_width=True)
        
        else:
            st.warning("No data available for comparison")
    
    except Exception as e:
        st.error(f"Error in price comparison: {e}")


def show_financial_comparison(tickers):
    """Display financial metrics comparison."""
    
    st.subheader('Financial Metrics Comparison')
    
    try:
        # Get financial data for all tickers
        financial_data = []
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                metrics = {
                    'Ticker': ticker,
                    'Market Cap': info.get('marketCap', None),
                    'P/E Ratio': info.get('trailingPE', None),
                    'Forward P/E': info.get('forwardPE', None),
                    'PEG Ratio': info.get('pegRatio', None),
                    'Price/Book': info.get('priceToBook', None),
                    'Profit Margin': info.get('profitMargins', None),
                    'Operating Margin': info.get('operatingMargins', None),
                    'ROE': info.get('returnOnEquity', None),
                    'ROA': info.get('returnOnAssets', None),
                    'Revenue Growth': info.get('revenueGrowth', None),
                    'Dividend Yield': info.get('dividendYield', None)
                }
                
                financial_data.append(metrics)
                
            except Exception as e:
                st.warning(f"Could not fetch financial data for {ticker}: {e}")
        
        if financial_data:
            # Create DataFrame
            df = pd.DataFrame(financial_data)
            df = df.set_index('Ticker')
            
            # Format the data
            format_dict = {
                'Market Cap': lambda x: f"${x:,.0f}" if pd.notnull(x) else 'N/A',
                'P/E Ratio': lambda x: f"{x:.2f}" if pd.notnull(x) else 'N/A',
                'Forward P/E': lambda x: f"{x:.2f}" if pd.notnull(x) else 'N/A',
                'PEG Ratio': lambda x: f"{x:.2f}" if pd.notnull(x) else 'N/A',
                'Price/Book': lambda x: f"{x:.2f}" if pd.notnull(x) else 'N/A',
                'Profit Margin': lambda x: f"{x:.2%}" if pd.notnull(x) else 'N/A',
                'Operating Margin': lambda x: f"{x:.2%}" if pd.notnull(x) else 'N/A',
                'ROE': lambda x: f"{x:.2%}" if pd.notnull(x) else 'N/A',
                'ROA': lambda x: f"{x:.2%}" if pd.notnull(x) else 'N/A',
                'Revenue Growth': lambda x: f"{x:.2%}" if pd.notnull(x) else 'N/A',
                'Dividend Yield': lambda x: f"{x:.2%}" if pd.notnull(x) else 'N/A'
            }
            
            formatted_df = df.copy()
            for col, format_func in format_dict.items():
                if col in formatted_df.columns:
                    formatted_df[col] = formatted_df[col].apply(format_func)
            
            st.dataframe(formatted_df)
            
            # Create visualizations for key metrics
            numeric_df = df.copy()
            
            # Valuation Metrics
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('P/E Ratio Comparison', 'PEG Ratio Comparison',
                              'Price/Book Comparison', 'Dividend Yield Comparison')
            )
            
            # P/E Ratio
            if 'P/E Ratio' in numeric_df.columns:
                fig.add_trace(
                    go.Bar(
                        x=numeric_df.index,
                        y=numeric_df['P/E Ratio'],
                        name='P/E Ratio'
                    ),
                    row=1, col=1
                )
            
            # PEG Ratio
            if 'PEG Ratio' in numeric_df.columns:
                fig.add_trace(
                    go.Bar(
                        x=numeric_df.index,
                        y=numeric_df['PEG Ratio'],
                        name='PEG Ratio'
                    ),
                    row=1, col=2
                )
            
            # Price/Book
            if 'Price/Book' in numeric_df.columns:
                fig.add_trace(
                    go.Bar(
                        x=numeric_df.index,
                        y=numeric_df['Price/Book'],
                        name='Price/Book'
                    ),
                    row=2, col=1
                )
            
            # Dividend Yield
            if 'Dividend Yield' in numeric_df.columns:
                fig.add_trace(
                    go.Bar(
                        x=numeric_df.index,
                        y=numeric_df['Dividend Yield'],
                        name='Dividend Yield'
                    ),
                    row=2, col=2
                )
            
            fig.update_layout(
                height=800,
                showlegend=False,
                template='plotly_dark'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Profitability Metrics
            fig = go.Figure()
            
            metrics = ['Profit Margin', 'Operating Margin', 'ROE', 'ROA']
            for metric in metrics:
                if metric in numeric_df.columns:
                    fig.add_trace(
                        go.Bar(
                            name=metric,
                            x=numeric_df.index,
                            y=numeric_df[metric]
                        )
                    )
            
            fig.update_layout(
                title='Profitability Metrics Comparison',
                barmode='group',
                yaxis_title='Ratio',
                template='plotly_dark',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.write("No financial data available for comparison")
    
    except Exception as e:
        st.error(f"Error in financial comparison: {e}")


def show_technical_comparison(tickers, period):
    """Display technical indicators comparison."""
    
    st.subheader('Technical Indicators Comparison')
    
    try:
        # Get data and calculate technical indicators for all tickers
        tech_data = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                
                if not hist.empty:
                    # Calculate technical indicators
                    hist['MA20'] = hist['Close'].rolling(window=20).mean()
                    hist['MA50'] = hist['Close'].rolling(window=50).mean()
                    hist['RSI'] = calculate_rsi(hist['Close'])
                    hist['MACD'], hist['Signal'] = calculate_macd(hist['Close'])
                    
                    tech_data[ticker] = hist
            
            except Exception as e:
                st.warning(f"Could not calculate technical indicators for {ticker}: {e}")
        
        if tech_data:
            # Create technical analysis visualizations
            for ticker, data in tech_data.items():
                st.write(f"**Technical Analysis - {ticker}**")
                
                # Create subplots for price with MA and indicators
                fig = make_subplots(
                    rows=3, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    subplot_titles=(f'{ticker} Price and Moving Averages', 'RSI', 'MACD'),
                    row_heights=[0.5, 0.25, 0.25]
                )
                
                # Price and MA
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['Close'],
                        name='Price',
                        line=dict(color='white')
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['MA20'],
                        name='MA20',
                        line=dict(color='orange')
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['MA50'],
                        name='MA50',
                        line=dict(color='blue')
                    ),
                    row=1, col=1
                )
                
                # RSI
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['RSI'],
                        name='RSI',
                        line=dict(color='purple')
                    ),
                    row=2, col=1
                )
                
                # Add RSI overbought/oversold lines
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                
                # MACD
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['MACD'],
                        name='MACD',
                        line=dict(color='blue')
                    ),
                    row=3, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['Signal'],
                        name='Signal',
                        line=dict(color='orange')
                    ),
                    row=3, col=1
                )
                
                # Update layout
                fig.update_layout(
                    height=800,
                    template='plotly_dark',
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                
                fig.update_yaxes(title_text="Price ($)", row=1, col=1)
                fig.update_yaxes(title_text="RSI", row=2, col=1)
                fig.update_yaxes(title_text="MACD", row=3, col=1)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display current technical signals
                current_price = data['Close'].iloc[-1]
                ma20 = data['MA20'].iloc[-1]
                ma50 = data['MA50'].iloc[-1]
                rsi = data['RSI'].iloc[-1]
                macd = data['MACD'].iloc[-1]
                signal = data['Signal'].iloc[-1]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Moving Averages**")
                    if current_price > ma20 and current_price > ma50:
                        st.markdown("🟢 Price above both MAs (Bullish)")
                    elif current_price < ma20 and current_price < ma50:
                        st.markdown("🔴 Price below both MAs (Bearish)")
                    else:
                        st.markdown("⚠️ Mixed MA signals")
                
                with col2:
                    st.write("**Technical Signals**")
                    # RSI
                    if rsi > 70:
                        st.markdown("🔴 RSI indicates overbought")
                    elif rsi < 30:
                        st.markdown("🟢 RSI indicates oversold")
                    else:
                        st.markdown("⚪ RSI in neutral zone")
                    
                    # MACD
                    if macd > signal:
                        st.markdown("🟢 MACD above signal line (Bullish)")
                    else:
                        st.markdown("🔴 MACD below signal line (Bearish)")
        
        else:
            st.write("No technical data available for comparison")
    
    except Exception as e:
        st.error(f"Error in technical comparison: {e}")


def show_correlation_analysis(tickers, period):
    """Display correlation analysis between stocks."""
    
    st.subheader('Correlation Analysis')
    
    try:
        # Get closing prices for all tickers
        prices_data = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                if not hist.empty:
                    prices_data[ticker] = hist['Close']
            except Exception as e:
                st.warning(f"Could not fetch data for {ticker}: {e}")
        
        if prices_data:
            # Create DataFrame with all closing prices
            df = pd.DataFrame(prices_data)
            
            # Calculate returns
            returns = df.pct_change()
            
            # Calculate correlation matrix
            correlation = returns.corr()
            
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
                title='Correlation Matrix',
                template='plotly_dark',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display correlation interpretation
            st.write("**Correlation Interpretation**")
            st.write("""
            - Correlation of 1.0: Perfect positive correlation
            - Correlation of -1.0: Perfect negative correlation
            - Correlation near 0: No correlation
            """)
            
            # Find highest and lowest correlations
            correlations = []
            for i in range(len(correlation.columns)):
                for j in range(i+1, len(correlation.columns)):
                    correlations.append({
                        'Stock 1': correlation.columns[i],
                        'Stock 2': correlation.columns[j],
                        'Correlation': correlation.iloc[i, j]
                    })
            
            if correlations:
                corr_df = pd.DataFrame(correlations)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Highest Correlations**")
                    highest_corr = corr_df.nlargest(3, 'Correlation')
                    for _, row in highest_corr.iterrows():
                        st.write(f"{row['Stock 1']} - {row['Stock 2']}: {row['Correlation']:.2f}")
                
                with col2:
                    st.write("**Lowest Correlations**")
                    lowest_corr = corr_df.nsmallest(3, 'Correlation')
                    for _, row in lowest_corr.iterrows():
                        st.write(f"{row['Stock 1']} - {row['Stock 2']}: {row['Correlation']:.2f}")
        
        else:
            st.write("No data available for correlation analysis")
    
    except Exception as e:
        st.error(f"Error in correlation analysis: {e}")


# Helper functions

def calculate_rsi(prices, periods=14):
    """Calculate Relative Strength Index."""
    
    delta = prices.diff()
    gain = (delta.clip(lower=0)).rolling(window=periods).mean()
    loss = (-delta.clip(upper=0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD and Signal line."""
    
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    
    return macd, signal_line 