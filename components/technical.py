import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('technical_analysis')

def log_function_call(func):
    """Decorator to log function calls and handle errors."""
    def wrapper(*args, **kwargs):
        try:
            logger.info(f"Starting {func.__name__}")
            result = func(*args, **kwargs)
            logger.info(f"Completed {func.__name__}")
            return result
        except Exception as e:
            error_msg = f"Error in {func.__name__}: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            st.error(f"An error occurred in {func.__name__}: {str(e)}")
            return None
    return wrapper

def show_technical_analysis(ticker_symbol, period, indicators):
    """Display technical analysis indicators."""
    
    st.header('Technical Analysis')
    logger.info(f"Analyzing technical indicators for {ticker_symbol} over {period}")
    
    try:
        # Get historical data
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period=period)
        
        if hist.empty:
            logger.warning(f"No historical data available for {ticker_symbol}")
            st.error(f"No historical data available for {ticker_symbol}")
            return
        
        logger.info(f"Successfully retrieved {len(hist)} data points for {ticker_symbol}")
        
        # Create tabs for different technical indicators
        tech_tabs = st.tabs(['Moving Averages', 'Oscillators', 'Volatility', 'Support/Resistance'])
        
        with tech_tabs[0]:
            if indicators.get('ma_periods'):
                logger.info(f"Calculating moving averages for periods: {indicators['ma_periods']}")
                show_moving_averages(hist, indicators['ma_periods'])
            else:
                logger.info("No moving average periods selected")
                st.info("Please select moving average periods in the sidebar.")
        
        with tech_tabs[1]:
            if indicators.get('show_rsi') or indicators.get('show_macd'):
                logger.info(f"Calculating oscillators - RSI: {indicators.get('show_rsi')}, MACD: {indicators.get('show_macd')}")
                show_oscillators(hist, show_rsi=indicators.get('show_rsi', False),
                               show_macd=indicators.get('show_macd', False))
            else:
                logger.info("No oscillators selected")
                st.info("Please enable RSI or MACD in the sidebar.")
        
        with tech_tabs[2]:
            if indicators.get('show_bollinger') or indicators.get('show_volatility'):
                logger.info("Calculating volatility indicators")
                show_volatility_indicators(hist, 
                                        show_bollinger=indicators.get('show_bollinger', False),
                                        show_volatility=indicators.get('show_volatility', False))
            else:
                logger.info("No volatility indicators selected")
                st.info("Please enable volatility indicators in the sidebar.")
        
        with tech_tabs[3]:
            logger.info("Calculating support and resistance levels")
            show_support_resistance(hist)
    
    except Exception as e:
        error_msg = f"Error in technical analysis for {ticker_symbol}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        st.error(f"Error in technical analysis: {str(e)}")


def show_moving_averages(hist, ma_periods):
    """Display moving averages analysis."""
    
    st.subheader('Moving Averages')
    
    # Add moving averages to the data
    for period in ma_periods:
        hist[f'MA_{period}'] = hist['Close'].rolling(window=period).mean()
    
    # Check for golden cross and death cross
    if 'MA_50' in hist.columns and 'MA_200' in hist.columns:
        # Check for golden cross (50-day crosses above 200-day)
        hist['Golden_Cross'] = (hist['MA_50'] > hist['MA_200']) & (hist['MA_50'].shift(1) <= hist['MA_200'].shift(1))
        
        # Check for death cross (50-day crosses below 200-day)
        hist['Death_Cross'] = (hist['MA_50'] < hist['MA_200']) & (hist['MA_50'].shift(1) >= hist['MA_200'].shift(1))
        
        # Find the most recent crosses
        golden_cross_dates = hist[hist['Golden_Cross']].index
        death_cross_dates = hist[hist['Death_Cross']].index
        
        # Display signals
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Golden Cross (Bullish Signal):**")
            if len(golden_cross_dates) > 0:
                most_recent = golden_cross_dates[-1]
                st.write(f"Most recent: {most_recent.strftime('%Y-%m-%d')}")
                
                # Calculate returns since the cross
                if most_recent in hist.index:
                    price_at_cross = hist.loc[most_recent, 'Close']
                    current_price = hist['Close'].iloc[-1]
                    pct_change = ((current_price - price_at_cross) / price_at_cross) * 100
                    st.write(f"Return since signal: {pct_change:.2f}%")
            else:
                st.write("No golden cross detected in this time period")
        
        with col2:
            st.write("**Death Cross (Bearish Signal):**")
            if len(death_cross_dates) > 0:
                most_recent = death_cross_dates[-1]
                st.write(f"Most recent: {most_recent.strftime('%Y-%m-%d')}")
                
                # Calculate returns since the cross
                if most_recent in hist.index:
                    price_at_cross = hist.loc[most_recent, 'Close']
                    current_price = hist['Close'].iloc[-1]
                    pct_change = ((current_price - price_at_cross) / price_at_cross) * 100
                    st.write(f"Return since signal: {pct_change:.2f}%")
            else:
                st.write("No death cross detected in this time period")
    
    # Create a plot with price and moving averages
    fig = go.Figure()
    
    # Add price
    fig.add_trace(
        go.Scatter(
            x=hist.index,
            y=hist['Close'],
            name='Close Price',
            line=dict(color='rgba(255, 255, 255, 0.8)', width=2)
        )
    )
    
    # Add moving averages
    colors = ['rgba(255, 165, 0, 0.8)', 'rgba(46, 139, 87, 0.8)', 'rgba(178, 34, 34, 0.8)']
    for i, period in enumerate(ma_periods):
        if f'MA_{period}' in hist.columns:
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist[f'MA_{period}'],
                    name=f'{period}-day MA',
                    line=dict(color=colors[i % len(colors)], width=1.5)
                )
            )
    
    # Highlight crosses if they exist
    if 'Golden_Cross' in hist.columns and 'Death_Cross' in hist.columns:
        # Add green markers for golden crosses
        golden_cross_points = hist[hist['Golden_Cross']]
        if not golden_cross_points.empty:
            fig.add_trace(
                go.Scatter(
                    x=golden_cross_points.index,
                    y=golden_cross_points['Close'],
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=15, color='green'),
                    name='Golden Cross (Buy)'
                )
            )
        
        # Add red markers for death crosses
        death_cross_points = hist[hist['Death_Cross']]
        if not death_cross_points.empty:
            fig.add_trace(
                go.Scatter(
                    x=death_cross_points.index,
                    y=death_cross_points['Close'],
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=15, color='red'),
                    name='Death Cross (Sell)'
                )
            )
    
    # Update layout
    fig.update_layout(
        title='Price with Moving Averages',
        yaxis_title='Price ($)',
        template='plotly_dark',
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("""
    **Moving Averages Interpretation:**
    - **Golden Cross (50-day MA crosses above 200-day MA)**: Considered a bullish signal indicating potential upward momentum
    - **Death Cross (50-day MA crosses below 200-day MA)**: Considered a bearish signal indicating potential downward momentum
    - **Price above longer-term MAs**: Generally bullish
    - **Price below longer-term MAs**: Generally bearish
    """)


def show_oscillators(hist, show_rsi=False, show_macd=False):
    """Display oscillator indicators like RSI and MACD."""
    
    st.subheader('Oscillators')
    
    if not show_rsi and not show_macd:
        st.info("Please enable RSI or MACD indicators in the sidebar.")
        return
    
    # Create subplot figure with appropriate number of rows
    num_rows = sum([show_rsi, show_macd])
    if num_rows == 0:
        return
    
    fig = make_subplots(
        rows=num_rows, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.1, 
        subplot_titles=([title for show, title in [(show_rsi, 'RSI (14)'), (show_macd, 'MACD')] if show]),
        row_heights=[1/num_rows] * num_rows
    )
    
    current_row = 1
    
    if show_rsi:
        # Calculate RSI
        hist['RSI'] = calculate_rsi(hist['Close'], periods=14)
        
        # Add RSI trace
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['RSI'],
                name='RSI',
                line=dict(color='purple', width=1.5)
            ),
            row=current_row, col=1
        )
        
        # Add RSI overbought/oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", name="Overbought", row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", name="Oversold", row=current_row, col=1)
        
        current_row += 1
    
    if show_macd:
        # Calculate MACD
        calculate_macd(hist)
        
        if 'MACD' in hist.columns and 'Signal' in hist.columns and 'Histogram' in hist.columns:
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['MACD'],
                    name='MACD',
                    line=dict(color='blue', width=1.5)
                ),
                row=current_row, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['Signal'],
                    name='Signal',
                    line=dict(color='orange', width=1.5)
                ),
                row=current_row, col=1
            )
            
            # Add histogram
            colors = ['green' if val >= 0 else 'red' for val in hist['Histogram']]
            fig.add_trace(
                go.Bar(
                    x=hist.index,
                    y=hist['Histogram'],
                    name='Histogram',
                    marker_color=colors
                ),
                row=current_row, col=1
            )
    
    # Update layout
    fig.update_layout(
        template='plotly_dark',
        height=300 * num_rows,
        hovermode='x unified',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    # Update y-axis ranges
    if show_rsi:
        fig.update_yaxes(range=[0, 100], title_text="RSI Value", row=1, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add interpretations
    if show_rsi:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**RSI Interpretation:**")
            
            # Get current RSI
            current_rsi = hist['RSI'].iloc[-1] if 'RSI' in hist.columns and len(hist) > 0 else None
            
            if current_rsi is not None:
                # Format with color based on RSI level
                if current_rsi > 70:
                    st.markdown(f"Current RSI: <span style='color:red; font-weight:bold'>{current_rsi:.2f}</span> (Overbought)", unsafe_allow_html=True)
                    st.write("The stock may be overbought, suggesting a potential pullback or correction.")
                elif current_rsi < 30:
                    st.markdown(f"Current RSI: <span style='color:green; font-weight:bold'>{current_rsi:.2f}</span> (Oversold)", unsafe_allow_html=True)
                    st.write("The stock may be oversold, suggesting a potential bounce or reversal.")
                else:
                    st.write(f"Current RSI: {current_rsi:.2f} (Neutral)")
                    st.write("The stock is neither overbought nor oversold, suggesting neutral momentum.")
    
    if show_macd:
        with col2:
            st.write("**MACD Interpretation:**")
            
            # Get current MACD values
            if 'MACD' in hist.columns and 'Signal' in hist.columns and len(hist) > 0:
                current_macd = hist['MACD'].iloc[-1]
                current_signal = hist['Signal'].iloc[-1]
                current_hist = hist['Histogram'].iloc[-1]
                
                # Determine if MACD is bullish or bearish
                if current_macd > current_signal:
                    st.markdown(f"MACD: <span style='color:green; font-weight:bold'>{current_macd:.3f}</span> (Bullish)", unsafe_allow_html=True)
                    st.write(f"MACD is above signal line, suggesting bullish momentum.")
                else:
                    st.markdown(f"MACD: <span style='color:red; font-weight:bold'>{current_macd:.3f}</span> (Bearish)", unsafe_allow_html=True)
                    st.write(f"MACD is below signal line, suggesting bearish momentum.")
                
                # Check for recent crossovers (within last 5 days)
                last_5_days = hist.tail(5)
                if any((last_5_days['MACD'] > last_5_days['Signal']) & (last_5_days['MACD'].shift(1) <= last_5_days['Signal'].shift(1))):
                    st.write("⚠️ Recent bullish crossover (buy signal)")
                elif any((last_5_days['MACD'] < last_5_days['Signal']) & (last_5_days['MACD'].shift(1) >= last_5_days['Signal'].shift(1))):
                    st.write("⚠️ Recent bearish crossover (sell signal)")


def show_volatility_indicators(hist, show_bollinger=False, show_volatility=False):
    """Display volatility indicators like Bollinger Bands and ATR."""
    
    st.subheader('Volatility Analysis')
    
    if not show_bollinger and not show_volatility:
        st.info("Please enable volatility indicators in the sidebar.")
        return
    
    if show_bollinger:
        # Calculate Bollinger Bands
        hist['MA_20'] = hist['Close'].rolling(window=20).mean()
        hist['Upper_Band'] = hist['MA_20'] + (hist['Close'].rolling(window=20).std() * 2)
        hist['Lower_Band'] = hist['MA_20'] - (hist['Close'].rolling(window=20).std() * 2)
        
        # Create figure for Bollinger Bands
        bb_fig = go.Figure()
        
        # Add price
        bb_fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['Close'],
                name='Close Price',
                line=dict(color='rgba(255, 255, 255, 0.8)', width=2)
            )
        )
        
        # Add Bollinger Bands
        bb_fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['MA_20'],
                name='20-day MA',
                line=dict(color='rgba(255, 165, 0, 0.8)', width=1.5)
            )
        )
        
        bb_fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['Upper_Band'],
                name='Upper Band',
                line=dict(color='rgba(173, 216, 230, 0.8)', width=1),
                fill=None
            )
        )
        
        bb_fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['Lower_Band'],
                name='Lower Band',
                line=dict(color='rgba(173, 216, 230, 0.8)', width=1),
                fill='tonexty'  # Fill area between upper and lower bands
            )
        )
        
        # Update layout
        bb_fig.update_layout(
            title='Bollinger Bands (20,2)',
            yaxis_title='Price ($)',
            template='plotly_dark',
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(bb_fig, use_container_width=True)
    
    if show_volatility:
        # Calculate ATR and Historical Volatility
        hist['ATR'] = calculate_atr(hist, window=14)
        hist['Returns'] = hist['Close'].pct_change()
        hist['Volatility_20'] = hist['Returns'].rolling(window=20).std() * np.sqrt(252) * 100  # Annualized volatility in %
        
        # Create figure for volatility metrics
        vol_fig = make_subplots(
            rows=2, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.1, 
            subplot_titles=('Historical Volatility (%)', 'ATR'),
            row_heights=[0.5, 0.5]
        )
        
        # Add volatility trace
        vol_fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['Volatility_20'],
                name='20-day Volatility',
                line=dict(color='purple', width=1.5)
            ),
            row=1, col=1
        )
        
        # Add ATR trace
        vol_fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['ATR'],
                name='ATR (14)',
                line=dict(color='orange', width=1.5)
            ),
            row=2, col=1
        )
        
        # Update layout
        vol_fig.update_layout(
            template='plotly_dark',
            height=400,
            hovermode='x unified',
            showlegend=True
        )
        
        st.plotly_chart(vol_fig, use_container_width=True)
    
    # Display current volatility metrics
    if show_bollinger or show_volatility:
        col1, col2 = st.columns(2)
        
        with col1:
            if show_bollinger:
                st.write("**Bollinger Band Analysis:**")
                
                # Calculate Bollinger Band width
                hist['BB_Width'] = (hist['Upper_Band'] - hist['Lower_Band']) / hist['MA_20'] * 100
                
                current_bb_width = hist['BB_Width'].iloc[-1] if 'BB_Width' in hist.columns and len(hist) > 0 else None
                avg_bb_width = hist['BB_Width'].mean() if 'BB_Width' in hist.columns and len(hist) > 0 else None
                
                if current_bb_width is not None and avg_bb_width is not None:
                    st.write(f"Current BB Width: {current_bb_width:.2f}%")
                    st.write(f"Average BB Width: {avg_bb_width:.2f}%")
                    
                    # Compare current to average
                    if current_bb_width > avg_bb_width * 1.2:
                        st.write("⚠️ High volatility period (wide bands)")
                    elif current_bb_width < avg_bb_width * 0.8:
                        st.write("📏 Low volatility period (narrow bands) - potential breakout setup")
                    
                    # Check position within bands
                    current_close = hist['Close'].iloc[-1]
                    upper_band = hist['Upper_Band'].iloc[-1]
                    lower_band = hist['Lower_Band'].iloc[-1]
                    
                    if current_close > upper_band:
                        st.write("Price is above upper band (potentially overbought)")
                    elif current_close < lower_band:
                        st.write("Price is below lower band (potentially oversold)")
        
        with col2:
            if show_volatility:
                st.write("**Volatility Metrics:**")
                
                current_vol = hist['Volatility_20'].iloc[-1] if 'Volatility_20' in hist.columns and len(hist) > 0 else None
                current_atr = hist['ATR'].iloc[-1] if 'ATR' in hist.columns and len(hist) > 0 else None
                
                if current_vol is not None:
                    st.write(f"20-day Historical Volatility: {current_vol:.2f}%")
                    
                    # Interpret volatility
                    if current_vol > 40:
                        st.write("🌋 Very high volatility - higher risk and potential for large price swings")
                    elif current_vol > 20:
                        st.write("📈 Moderate volatility - typical for most stocks")
                    else:
                        st.write("🌊 Low volatility - more stable price action")
                
                if current_atr is not None:
                    st.write(f"Average True Range (ATR): ${current_atr:.2f}")
                    
                    # Calculate ATR as percentage of price
                    atr_pct = (current_atr / hist['Close'].iloc[-1]) * 100
                    st.write(f"ATR as % of price: {atr_pct:.2f}%")
                    
                    # Interpret ATR
                    st.write(f"Expected daily price range: ${hist['Close'].iloc[-1] - current_atr:.2f} to ${hist['Close'].iloc[-1] + current_atr:.2f}")


def show_support_resistance(hist):
    """Display support and resistance levels."""
    
    st.subheader('Support & Resistance Levels')
    
    # Identify support and resistance levels using zigzag method
    pivot_points = identify_pivot_points(hist, window=10)
    
    if not pivot_points.empty:
        # Create price chart with support/resistance levels
        fig = go.Figure()
        
        # Add price
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['Close'],
                name='Close Price',
                line=dict(color='rgba(255, 255, 255, 0.8)', width=2)
            )
        )
        
        # Add pivot high points (resistance)
        pivot_highs = pivot_points[pivot_points['Type'] == 'High']
        if not pivot_highs.empty:
            fig.add_trace(
                go.Scatter(
                    x=pivot_highs.index,
                    y=pivot_highs['Value'],
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=12, color='red'),
                    name='Resistance'
                )
            )
        
        # Add pivot low points (support)
        pivot_lows = pivot_points[pivot_points['Type'] == 'Low']
        if not pivot_lows.empty:
            fig.add_trace(
                go.Scatter(
                    x=pivot_lows.index,
                    y=pivot_lows['Value'],
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=12, color='green'),
                    name='Support'
                )
            )
        
        # Add horizontal lines for key levels
        add_key_horizontal_levels(fig, hist, pivot_points)
        
        # Update layout
        fig.update_layout(
            title='Price with Support & Resistance Levels',
            yaxis_title='Price ($)',
            template='plotly_dark',
            height=600,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Explain key levels
        st.write("**Key Support & Resistance Analysis:**")
        
        # Show current strong levels
        strong_levels = identify_strong_levels(hist, pivot_points)
        
        if strong_levels:
            st.write("**Strong levels to watch:**")
            
            current_price = hist['Close'].iloc[-1]
            levels_above = [level for level in strong_levels if level > current_price]
            levels_below = [level for level in strong_levels if level < current_price]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Resistance above:**")
                if levels_above:
                    # Sort and get the nearest level first
                    levels_above.sort()
                    for i, level in enumerate(levels_above[:3]):  # Show top 3 nearest levels
                        distance = ((level - current_price) / current_price) * 100
                        st.write(f"${level:.2f} ({distance:.2f}% away)")
                else:
                    st.write("No significant resistance identified")
            
            with col2:
                st.write("**Support below:**")
                if levels_below:
                    # Sort in reverse and get the nearest level first
                    levels_below.sort(reverse=True)
                    for i, level in enumerate(levels_below[:3]):  # Show top 3 nearest levels
                        distance = ((current_price - level) / current_price) * 100
                        st.write(f"${level:.2f} ({distance:.2f}% away)")
                else:
                    st.write("No significant support identified")
        
        else:
            st.write("No significant support or resistance levels identified.")
    
    else:
        st.write("Insufficient data to identify support and resistance levels.")


# Helper functions for technical analysis

@log_function_call
def calculate_rsi(prices, periods=14):
    """Calculate Relative Strength Index."""
    logger.info(f"Calculating RSI with period {periods}")
    
    try:
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=periods).mean()
        avg_loss = loss.rolling(window=periods).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        logger.info("RSI calculation completed successfully")
        return rsi
    
    except Exception as e:
        logger.error(f"Error calculating RSI: {str(e)}\n{traceback.format_exc()}")
        raise


@log_function_call
def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculate MACD, Signal, and Histogram for a given dataframe."""
    logger.info(f"Calculating MACD with fast={fast}, slow={slow}, signal={signal}")
    
    try:
        df['EMA_fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
        df['EMA_slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = df['EMA_fast'] - df['EMA_slow']
        df['Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        df['Histogram'] = df['MACD'] - df['Signal']
        
        logger.info("MACD calculation completed successfully")
        return df
    
    except Exception as e:
        logger.error(f"Error calculating MACD: {str(e)}\n{traceback.format_exc()}")
        raise


@log_function_call
def calculate_atr(df, window=14):
    """Calculate Average True Range."""
    logger.info(f"Calculating ATR with window {window}")
    
    try:
        high = df['High']
        low = df['Low']
        close = df['Close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        atr = tr.rolling(window=window).mean()
        
        logger.info("ATR calculation completed successfully")
        return atr
    
    except Exception as e:
        logger.error(f"Error calculating ATR: {str(e)}\n{traceback.format_exc()}")
        raise


def identify_pivot_points(df, window=10):
    """Identify pivot points (highs and lows) in the price series."""
    
    # Create a copy to avoid modifying the original
    pivot_df = pd.DataFrame()
    
    # Get the highs and lows
    high = df['High']
    low = df['Low']
    
    # Initialize pivot points series
    pivot_points = pd.DataFrame(columns=['Value', 'Type'])
    
    # Find pivot highs
    for i in range(window, len(df) - window):
        if all(high.iloc[i] > high.iloc[i-j] for j in range(1, window+1)) and \
           all(high.iloc[i] > high.iloc[i+j] for j in range(1, window+1)):
            pivot_points.loc[df.index[i]] = [high.iloc[i], 'High']
    
    # Find pivot lows
    for i in range(window, len(df) - window):
        if all(low.iloc[i] < low.iloc[i-j] for j in range(1, window+1)) and \
           all(low.iloc[i] < low.iloc[i+j] for j in range(1, window+1)):
            pivot_points.loc[df.index[i]] = [low.iloc[i], 'Low']
    
    return pivot_points


def add_key_horizontal_levels(fig, df, pivot_points):
    """Add key horizontal support and resistance levels."""
    
    current_price = df['Close'].iloc[-1]
    price_range = df['High'].max() - df['Low'].min()
    
    # Function to check if two price levels are very close
    def is_close(p1, p2, threshold_pct=0.01):
        return abs(p1 - p2) / p1 < threshold_pct
    
    # Get strong levels that have been tested multiple times
    strong_levels = identify_strong_levels(df, pivot_points)
    
    # Add horizontal lines for important levels
    for level in strong_levels:
        # Only show levels within a reasonable range of current price
        if abs(level - current_price) / current_price < 0.15:  # Within 15% of current price
            # Color based on whether it's above or below current price
            color = 'red' if level > current_price else 'green'
            
            fig.add_shape(
                type='line',
                x0=df.index[0],
                y0=level,
                x1=df.index[-1],
                y1=level,
                line=dict(color=color, width=1, dash='dash'),
            )


def identify_strong_levels(df, pivot_points):
    """Identify strong support and resistance levels based on price clusters."""
    
    price_range = df['High'].max() - df['Low'].min()
    
    # Extract all pivot point values
    all_pivots = pivot_points['Value'].tolist()
    
    # Define a function to find clusters
    def find_clusters(values, threshold_pct=0.01):
        if not values:
            return []
        
        # Sort values
        sorted_values = sorted(values)
        
        # Initialize clusters
        clusters = []
        current_cluster = [sorted_values[0]]
        
        # Group close values
        for value in sorted_values[1:]:
            if is_close(value, current_cluster[-1], threshold_pct):
                current_cluster.append(value)
            else:
                # If cluster has at least 2 points, add it
                if len(current_cluster) >= 2:
                    clusters.append(sum(current_cluster) / len(current_cluster))
                
                # Start a new cluster
                current_cluster = [value]
        
        # Add the last cluster if it has at least 2 points
        if len(current_cluster) >= 2:
            clusters.append(sum(current_cluster) / len(current_cluster))
        
        return clusters
    
    # Function to check if two price levels are very close
    def is_close(p1, p2, threshold_pct=0.01):
        return abs(p1 - p2) / p1 < threshold_pct
    
    # Find strong levels
    strong_levels = find_clusters(all_pivots)
    
    return strong_levels 