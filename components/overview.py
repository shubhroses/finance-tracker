import streamlit as st
import yfinance as yf
import pandas as pd

def show_company_overview(ticker_symbol, info):
    """Display company overview information."""
    
    st.header('Company Overview')
    
    try:
        # Create two columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Company Description
            st.subheader('About the Company')
            st.write(info.get('longBusinessSummary', 'No description available.'))
            
            # Industry & Sector
            st.subheader('Classification')
            industry_col, sector_col = st.columns(2)
            with industry_col:
                st.write('**Industry:**')
                st.write(info.get('industry', 'N/A'))
            with sector_col:
                st.write('**Sector:**')
                st.write(info.get('sector', 'N/A'))
            
            # Website
            st.subheader('Website')
            website = info.get('website', '')
            if website:
                st.markdown(f"[{website}]({website})")
            else:
                st.write('N/A')
        
        with col2:
            # Key Statistics
            st.subheader('Key Statistics')
            
            # Market Data
            st.write('**Market Data**')
            metrics = {
                'Market Cap': f"${info.get('marketCap', 0):,.0f}",
                'Current Price': f"${info.get('currentPrice', 0):.2f}",
                'Volume': f"{info.get('volume', 0):,.0f}",
                'Avg Volume': f"{info.get('averageVolume', 0):,.0f}"
            }
            
            for label, value in metrics.items():
                if value != '$0.00' and value != '0':
                    st.metric(label, value)
                else:
                    st.metric(label, 'N/A')
            
            # Trading Information
            st.write('**Trading Information**')
            trading_info = {
                '52 Week High': f"${info.get('fiftyTwoWeekHigh', 0):.2f}",
                '52 Week Low': f"${info.get('fiftyTwoWeekLow', 0):.2f}",
                'Beta': f"{info.get('beta', 0):.2f}",
                'PE Ratio': f"{info.get('trailingPE', 0):.2f}"
            }
            
            for label, value in trading_info.items():
                if value != '$0.00' and value != '0.00':
                    st.metric(label, value)
                else:
                    st.metric(label, 'N/A')
    
    except Exception as e:
        st.error(f"Error displaying company overview: {str(e)}")
        st.info("Some company information may not be available.") 