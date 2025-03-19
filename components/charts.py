import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .utils import get_stock_history

def show_price_charts(ticker_symbol, period="1y"):
    # Get historical data with rate limiting
    df = get_stock_history(ticker_symbol, period)
    
    if df is None or df.empty:
        st.error(f"Unable to fetch price data for {ticker_symbol}. Please try again later.")
        return

    # Create figure with secondary y-axis
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                       vertical_spacing=0.03, 
                       row_heights=[0.7, 0.3])

    # Add candlestick chart
    fig.add_trace(go.Candlestick(x=df.index,
                                open=df['Open'],
                                high=df['High'],
                                low=df['Low'],
                                close=df['Close'],
                                name='OHLC'),
                  row=1, col=1)

    # Add volume bar chart
    fig.add_trace(go.Bar(x=df.index, 
                        y=df['Volume'],
                        name='Volume',
                        marker_color='rgba(0,0,255,0.3)'),
                  row=2, col=1)

    # Update layout
    fig.update_layout(
        title=f'{ticker_symbol} Stock Price',
        yaxis_title='Stock Price (USD)',
        yaxis2_title='Volume',
        xaxis_rangeslider_visible=False,
        height=800
    )

    st.plotly_chart(fig, use_container_width=True)


def highlight_significant_price_changes(fig, hist, row=1, col=1):
    """Add annotations for significant price changes."""
    
    # Calculate daily returns
    hist['Return'] = hist['Close'].pct_change() * 100
    
    # Identify significant movements (e.g., > +/-3%)
    significant_up = hist[hist['Return'] > 3]
    significant_down = hist[hist['Return'] < -3]
    
    # Limit to 5 most significant up and down movements to avoid cluttering
    significant_up = significant_up.nlargest(5, 'Return')
    significant_down = significant_down.nsmallest(5, 'Return')
    
    # Add annotations for significant up movements
    for date, row_data in significant_up.iterrows():
        fig.add_annotation(
            x=date,
            y=row_data['High'] * 1.02,  # Place annotation slightly above high price
            text=f"+{row_data['Return']:.1f}%",
            showarrow=True,
            arrowhead=1,
            arrowsize=0.5,
            arrowwidth=1,
            arrowcolor="green",
            font=dict(color="green", size=10),
            row=row, col=col
        )
    
    # Add annotations for significant down movements
    for date, row_data in significant_down.iterrows():
        fig.add_annotation(
            x=date,
            y=row_data['Low'] * 0.98,  # Place annotation slightly below low price
            text=f"{row_data['Return']:.1f}%",
            showarrow=True,
            arrowhead=1,
            arrowsize=0.5,
            arrowwidth=1,
            arrowcolor="red",
            font=dict(color="red", size=10),
            row=row, col=col
        ) 