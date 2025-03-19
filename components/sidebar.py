import streamlit as st

def create_sidebar():
    """Create the sidebar with input options and return user selections."""
    
    st.sidebar.header('Navigation')
    tab_selection = st.sidebar.radio(
        "Select Analysis Type",
        ["Stock Analysis", "Compare Stocks", "Portfolio Analysis"]
    )
    
    # Stock selection (for single stock analysis)
    if tab_selection == "Stock Analysis":
        st.sidebar.header('Stock Selection')
        ticker_symbol = st.sidebar.text_input('Enter Stock Ticker', 'AAPL')
        period = st.sidebar.selectbox(
            'Select Time Period', 
            ['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'], 
            index=3
        )
        
        # Technical indicator selection (will be used in technical analysis)
        st.sidebar.header('Technical Indicators')
        
        # Moving Averages
        show_ma = st.sidebar.checkbox('Show Moving Averages', True)
        if show_ma:
            ma_periods = st.sidebar.multiselect(
                'Select MA Periods',
                [5, 10, 20, 50, 100, 200],
                default=[20, 50, 200]
            )
        else:
            ma_periods = []
        
        # Add indicators options
        show_rsi = st.sidebar.checkbox('Show RSI', True)
        show_macd = st.sidebar.checkbox('Show MACD', True)
        show_bollinger = st.sidebar.checkbox('Show Bollinger Bands', True)
        
        # Risk analysis options
        st.sidebar.header('Risk Analysis')
        show_volatility = st.sidebar.checkbox('Show Volatility', True)
        show_drawdown = st.sidebar.checkbox('Show Max Drawdown', True)
        
        return {
            'tab_selection': tab_selection,
            'ticker_symbol': ticker_symbol,
            'period': period,
            'ma_periods': ma_periods,
            'show_rsi': show_rsi,
            'show_macd': show_macd,
            'show_bollinger': show_bollinger,
            'show_volatility': show_volatility,
            'show_drawdown': show_drawdown
        }
    
    # Return only tab selection for other tabs
    return {'tab_selection': tab_selection} 