import streamlit as st
from .utils import get_stock_info

def show_company_overview(ticker_symbol, info=None):
    if info is None:
        info = get_stock_info(ticker_symbol)
    
    if not info:
        st.error(f"Unable to fetch data for {ticker_symbol}. Please try again later.")
        return

    # Display company information
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Company Overview")
        st.write(info.get('longBusinessSummary', 'No company description available.'))
    
    with col2:
        metrics = {
            "Market Cap": info.get('marketCap', 'N/A'),
            "P/E Ratio": info.get('trailingPE', 'N/A'),
            "52 Week High": info.get('fiftyTwoWeekHigh', 'N/A'),
            "52 Week Low": info.get('fiftyTwoWeekLow', 'N/A'),
            "Volume": info.get('volume', 'N/A'),
            "Avg Volume": info.get('averageVolume', 'N/A')
        }
        
        for label, value in metrics.items():
            if isinstance(value, (int, float)):
                if label == "Market Cap":
                    value = f"${value:,.0f}"
                elif label in ["52 Week High", "52 Week Low"]:
                    value = f"${value:.2f}"
                elif "Volume" in label:
                    value = f"{value:,.0f}"
                else:
                    value = f"{value:.2f}"
            st.metric(label, value)

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