import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

def show_price_charts(ticker_symbol, period):
    """Display price and volume charts."""
    
    st.header('Price Charts')
    
    try:
        # Get historical data
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period=period)
        
        if not hist.empty:
            # Create figure with secondary y-axis
            fig = make_subplots(rows=2, cols=1, 
                              shared_xaxes=True,
                              vertical_spacing=0.03,
                              subplot_titles=('Price', 'Volume'),
                              row_heights=[0.7, 0.3])

            # Add candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'],
                    name='OHLC'
                ),
                row=1, col=1
            )

            # Add volume bar chart
            colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in hist.iterrows()]
            fig.add_trace(
                go.Bar(
                    x=hist.index,
                    y=hist['Volume'],
                    name='Volume',
                    marker_color=colors
                ),
                row=2, col=1
            )

            # Update layout
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                height=800,
                template='plotly_dark',
                showlegend=False
            )

            # Update y-axes labels
            fig.update_yaxes(title_text="Price ($)", row=1, col=1)
            fig.update_yaxes(title_text="Volume", row=2, col=1)

            st.plotly_chart(fig, use_container_width=True)

            # Add price statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Current",
                    f"${hist['Close'][-1]:.2f}",
                    f"{((hist['Close'][-1] - hist['Close'][-2]) / hist['Close'][-2] * 100):.2f}%"
                )
            
            with col2:
                st.metric(
                    "Period High",
                    f"${hist['High'].max():.2f}"
                )
            
            with col3:
                st.metric(
                    "Period Low",
                    f"${hist['Low'].min():.2f}"
                )

            # Add volume statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Average Volume",
                    f"{hist['Volume'].mean():,.0f}"
                )
            
            with col2:
                st.metric(
                    "Max Volume",
                    f"{hist['Volume'].max():,.0f}"
                )

        else:
            st.error("No historical data available for the selected period.")

    except Exception as e:
        st.error(f"Error displaying price charts: {str(e)}")
        st.info("Unable to load price chart data. Please try again later.")


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