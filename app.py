import streamlit as st
import yfinance as yf
from components.sidebar import create_sidebar
from components.overview import show_company_overview
from components.charts import show_price_charts
from components.technical import show_technical_analysis
from components.financials import show_financial_metrics
from components.comparison import show_stock_comparison
from components.portfolio import show_portfolio_analyzer
from components.news import show_news_sentiment
from components.utils import get_stock_info

# Disable file watcher in production
st.set_option('server.fileWatcherType', 'none')

# Set page config
st.set_page_config(
    page_title="Finance Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
    <style>
    /* Main app */
    .main {
        background-color: #0E1117;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #1E2127;
        padding: 2rem 1rem;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #E0E0E0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    h1 {
        text-align: center;
        background: linear-gradient(90deg, #1E88E5 0%, #1565C0 100%);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Tabs styling */
    .stTabs {
        background: transparent !important;
        padding: 1rem 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1E2127;
        border-radius: 5px;
        padding: 1rem;
        margin-top: 1rem;
    }
    
    /* Metrics styling */
    div[data-testid="stMetricValue"] {
        background-color: #262730;
        padding: 1rem;
        border-radius: 5px;
        font-size: 1.5rem !important;
        color: #E0E0E0 !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #262730;
        border-radius: 5px;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #1565C0;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #1E88E5;
        border: none;
    }
    
    /* DataFrame styling */
    .dataframe {
        background-color: #262730;
        border-radius: 5px;
        padding: 1rem;
    }
    
    /* Warning/Error/Info messages */
    .stAlert {
        background-color: #262730;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Links */
    a {
        color: #1E88E5 !important;
        text-decoration: none;
    }
    
    a:hover {
        color: #90CAF9 !important;
        text-decoration: underline;
    }
    
    /* Plotly chart background */
    .js-plotly-plot {
        background-color: #262730;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Sidebar text */
    .css-17lntkn {
        color: #E0E0E0;
    }
    
    /* Input fields */
    .stTextInput > div > div {
        background-color: #262730;
        border-radius: 5px;
        border: 1px solid #404040;
        color: #E0E0E0;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background-color: #262730;
        border-radius: 5px;
        border: 1px solid #404040;
        color: #E0E0E0;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # Create sidebar and get user inputs
    sidebar_inputs = create_sidebar()
    
    # Get values from sidebar inputs
    tab_selection = sidebar_inputs.get('tab_selection')
    ticker_symbol = sidebar_inputs.get('ticker_symbol')
    period = sidebar_inputs.get('period')
    
    # Handle Compare Stocks and Portfolio Analysis independently
    if tab_selection == "Compare Stocks":
        show_stock_comparison()
        return
    elif tab_selection == "Portfolio Analysis":
        show_portfolio_analyzer()
        return
    
    if ticker_symbol:
        try:
            # Get stock data with rate limiting
            info = get_stock_info(ticker_symbol)
            
            if info:
                # Display header with company info
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.title(f"{info.get('longName', ticker_symbol)} ({ticker_symbol})")
            
                if tab_selection == "Stock Analysis":
                    # Create tabs for different analyses
                    tabs = st.tabs([
                        "📊 Overview",
                        "📈 Charts",
                        "📉 Technical Analysis",
                        "💰 Financials",
                        "📰 News & Sentiment"
                    ])
                    
                    with tabs[0]:
                        show_company_overview(ticker_symbol, info)
                    
                    with tabs[1]:
                        show_price_charts(ticker_symbol, period)
                    
                    with tabs[2]:
                        # Get technical indicators from sidebar inputs
                        technical_indicators = {
                            'ma_periods': sidebar_inputs.get('ma_periods', []),
                            'show_rsi': sidebar_inputs.get('show_rsi', False),
                            'show_macd': sidebar_inputs.get('show_macd', False),
                            'show_bollinger': sidebar_inputs.get('show_bollinger', False),
                            'show_volatility': sidebar_inputs.get('show_volatility', False),
                            'show_drawdown': sidebar_inputs.get('show_drawdown', False)
                        }
                        show_technical_analysis(ticker_symbol, period, technical_indicators)
                    
                    with tabs[3]:
                        show_financial_metrics(ticker_symbol, info)
                    
                    with tabs[4]:
                        show_news_sentiment(ticker_symbol)
            else:
                st.error(f"Unable to fetch data for {ticker_symbol}. Please try again later.")
        
        except Exception as e:
            st.error(f"Error fetching data for {ticker_symbol}: {str(e)}")
            st.error("Please try again or check if the ticker symbol is correct.")
    
    else:
        # Display welcome message and instructions
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h1>Welcome to Finance Tracker 📈</h1>
            <p style="font-size: 1.2rem; color: #E0E0E0;">
                Your comprehensive tool for stock analysis and portfolio management
            </p>
        </div>
        
        <div style="background-color: #262730; padding: 2rem; border-radius: 10px; margin: 2rem 0;">
            <h2>Features</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                <div style="background-color: #1E2127; padding: 1rem; border-radius: 5px;">
                    <h3>📊 Single Stock Analysis</h3>
                    <p>Detailed analysis of individual stocks with comprehensive metrics and visualizations</p>
                </div>
                <div style="background-color: #1E2127; padding: 1rem; border-radius: 5px;">
                    <h3>🔄 Stock Comparison</h3>
                    <p>Compare multiple stocks side by side with interactive charts and metrics</p>
                </div>
                <div style="background-color: #1E2127; padding: 1rem; border-radius: 5px;">
                    <h3>💼 Portfolio Analysis</h3>
                    <p>Track and analyze your investment portfolio with advanced analytics</p>
                </div>
            </div>
        </div>
        
        <div style="background-color: #262730; padding: 2rem; border-radius: 10px;">
            <h2>Getting Started</h2>
            <ol style="color: #E0E0E0;">
                <li>Select an analysis type from the sidebar</li>
                <li>Enter a stock ticker symbol</li>
                <li>Choose your preferred time period and indicators</li>
            </ol>
            
            <h3>Available Analysis Tools</h3>
            <ul style="color: #E0E0E0; list-style-type: none; padding: 0;">
                <li>📊 Company Overview</li>
                <li>📈 Price Charts</li>
                <li>📉 Technical Analysis</li>
                <li>💰 Financial Metrics</li>
                <li>📰 News & Sentiment Analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 