import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from .utils import get_stock_financials

def format_currency(value):
    """Format large numbers in billions/millions"""
    if value is None or pd.isna(value):
        return "N/A"
    
    billion = 1_000_000_000
    million = 1_000_000
    
    if abs(value) >= billion:
        return f"${value/billion:.2f}B"
    elif abs(value) >= million:
        return f"${value/million:.2f}M"
    else:
        return f"${value:,.2f}"

def format_financial_statement(df):
    """Format financial statement dataframe and handle date parsing"""
    if df is None or df.empty:
        return None
        
    try:
        # Convert index to string to avoid any potential parsing issues
        df.index = df.index.astype(str)
        
        # Ensure all data is numeric
        df = df.apply(pd.to_numeric, errors='coerce')
        
        # Sort columns in descending order (most recent first)
        df = df.sort_index(axis=1, ascending=False)
        
        return df
    except Exception as e:
        st.error(f"Error formatting financial statement: {str(e)}")
        return None

def create_financial_chart(df, title, metrics):
    """Create a financial chart with the specified metrics"""
    if df is None or df.empty:
        return None
        
    fig = go.Figure()
    
    for metric in metrics:
        if metric in df.index:
            values = df.loc[metric]
            fig.add_trace(go.Bar(
                name=metric,
                x=values.index,
                y=values.values,
                text=[format_currency(x) for x in values.values],
                textposition='auto',
            ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        barmode='group',
        template="plotly_dark",
        showlegend=True,
        height=600,
        hovermode='x unified'
    )
    
    return fig

def show_financial_metrics(ticker_symbol, info=None):
    """Display financial metrics for a given stock"""
    st.header("Financial Analysis")
    
    # Get financial statements
    financial_data = get_stock_financials(ticker_symbol)
    
    if financial_data is None:
        st.error("Unable to fetch financial data. Please try again later.")
        return
        
    income_stmt, balance_sheet, cash_flow = financial_data
    
    # Format financial statements
    income_stmt = format_financial_statement(income_stmt)
    balance_sheet = format_financial_statement(balance_sheet)
    cash_flow = format_financial_statement(cash_flow)
    
    # Create tabs for different financial statements
    fin_tabs = st.tabs(["📊 Key Metrics", "💰 Income Statement", "📑 Balance Sheet", "💵 Cash Flow"])
    
    with fin_tabs[0]:
        if info:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Market Cap", format_currency(info.get('marketCap')))
                st.metric("Revenue (TTM)", format_currency(info.get('totalRevenue')))
                st.metric("Gross Profit (TTM)", format_currency(info.get('grossProfits')))
            
            with col2:
                st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A'):.2f}" if info.get('trailingPE') else "N/A")
                st.metric("Forward P/E", f"{info.get('forwardPE', 'N/A'):.2f}" if info.get('forwardPE') else "N/A")
                st.metric("PEG Ratio", f"{info.get('pegRatio', 'N/A'):.2f}" if info.get('pegRatio') else "N/A")
            
            with col3:
                st.metric("Profit Margin", f"{info.get('profitMargins', 0)*100:.2f}%" if info.get('profitMargins') else "N/A")
                st.metric("Operating Margin", f"{info.get('operatingMargins', 0)*100:.2f}%" if info.get('operatingMargins') else "N/A")
                st.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "N/A")
    
    with fin_tabs[1]:
        if income_stmt is not None and not income_stmt.empty:
            st.subheader("Income Statement Analysis")
            
            # Create metrics for income statement
            income_metrics = [
                'Total Revenue',
                'Gross Profit',
                'Operating Income',
                'Net Income',
                'EBITDA'
            ]
            
            fig = create_financial_chart(income_stmt, "Key Income Statement Metrics Over Time", income_metrics)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Display raw data in expandable section
            with st.expander("View Raw Data"):
                st.dataframe(income_stmt.style.format("${:,.2f}"))
        else:
            st.warning("No income statement data available")
    
    with fin_tabs[2]:
        if balance_sheet is not None and not balance_sheet.empty:
            st.subheader("Balance Sheet Analysis")
            
            # Create metrics for balance sheet
            balance_metrics = [
                'Total Assets',
                'Total Current Assets',
                'Total Liabilities Net Minority Interest',
                'Total Current Liabilities',
                'Total Equity'
            ]
            
            fig = create_financial_chart(balance_sheet, "Key Balance Sheet Metrics Over Time", balance_metrics)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Display raw data in expandable section
            with st.expander("View Raw Data"):
                st.dataframe(balance_sheet.style.format("${:,.2f}"))
        else:
            st.warning("No balance sheet data available")
    
    with fin_tabs[3]:
        if cash_flow is not None and not cash_flow.empty:
            st.subheader("Cash Flow Analysis")
            
            # Create metrics for cash flow
            cash_flow_metrics = [
                'Operating Cash Flow',
                'Free Cash Flow',
                'Cash Flow From Continuing Operating Activities',
                'Capital Expenditure',
                'Cash Flow From Financing Activities'
            ]
            
            fig = create_financial_chart(cash_flow, "Key Cash Flow Metrics Over Time", cash_flow_metrics)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Display raw data in expandable section
            with st.expander("View Raw Data"):
                st.dataframe(cash_flow.style.format("${:,.2f}"))
        else:
            st.warning("No cash flow data available") 