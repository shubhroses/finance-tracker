import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import traceback

def show_financial_metrics(ticker_symbol, info):
    """Display financial metrics and analysis."""
    
    st.header('Financial Analysis')
    
    try:
        # Get stock data
        stock = yf.Ticker(ticker_symbol)
        
        # Create tabs for different financial metrics
        fin_tabs = st.tabs([
            "Key Metrics",
            "Income Statement",
            "Balance Sheet",
            "Cash Flow",
            "Financial Ratios"
        ])
        
        with fin_tabs[0]:
            show_key_metrics(info)
        
        with fin_tabs[1]:
            show_income_statement(stock)
        
        with fin_tabs[2]:
            show_balance_sheet(ticker_symbol, info)
        
        with fin_tabs[3]:
            show_cash_flow(stock)
        
        with fin_tabs[4]:
            show_financial_ratios(info)
            
    except Exception as e:
        st.error(f"Error fetching financial data: {str(e)}")
        st.info("Some financial data may not be available for this stock.")

def show_key_metrics(info):
    """Display key financial metrics."""
    
    st.subheader("Key Financial Metrics")
    
    # Create columns for metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Market Cap", f"${info.get('marketCap', 'N/A'):,.0f}" if info.get('marketCap') else "N/A")
        st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A'):.2f}" if info.get('trailingPE') else "N/A")
        st.metric("Forward P/E", f"{info.get('forwardPE', 'N/A'):.2f}" if info.get('forwardPE') else "N/A")
    
    with col2:
        st.metric("Revenue (TTM)", f"${info.get('totalRevenue', 'N/A'):,.0f}" if info.get('totalRevenue') else "N/A")
        st.metric("Profit Margin", f"{info.get('profitMargins', 'N/A'):.2%}" if info.get('profitMargins') else "N/A")
        st.metric("Operating Margin", f"{info.get('operatingMargins', 'N/A'):.2%}" if info.get('operatingMargins') else "N/A")
    
    with col3:
        st.metric("Dividend Yield", f"{info.get('dividendYield', 'N/A'):.2%}" if info.get('dividendYield') else "N/A")
        st.metric("Beta", f"{info.get('beta', 'N/A'):.2f}" if info.get('beta') else "N/A")
        st.metric("52 Week Range", f"${info.get('fiftyTwoWeekLow', 'N/A'):.2f} - ${info.get('fiftyTwoWeekHigh', 'N/A'):.2f}" if info.get('fiftyTwoWeekLow') and info.get('fiftyTwoWeekHigh') else "N/A")

def show_income_statement(stock):
    """Display income statement analysis."""
    
    st.subheader("Income Statement Analysis")
    
    try:
        # Get income statement data
        income_stmt = stock.financials
        
        if not income_stmt.empty:
            # Calculate year-over-year growth
            yoy_growth = income_stmt.pct_change(axis=1) * 100
            
            # Create visualization
            fig = make_subplots(rows=2, cols=1,
                              subplot_titles=("Revenue & Net Income", "Year-over-Year Growth"),
                              vertical_spacing=0.15)
            
            # Add Revenue and Net Income traces
            fig.add_trace(
                go.Bar(
                    x=income_stmt.columns,
                    y=income_stmt.loc['Total Revenue'],
                    name='Revenue',
                    marker_color='lightblue'
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Bar(
                    x=income_stmt.columns,
                    y=income_stmt.loc['Net Income'],
                    name='Net Income',
                    marker_color='darkblue'
                ),
                row=1, col=1
            )
            
            # Add growth rate traces
            fig.add_trace(
                go.Scatter(
                    x=yoy_growth.columns,
                    y=yoy_growth.loc['Total Revenue'],
                    name='Revenue Growth',
                    line=dict(color='lightblue')
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=yoy_growth.columns,
                    y=yoy_growth.loc['Net Income'],
                    name='Net Income Growth',
                    line=dict(color='darkblue')
                ),
                row=2, col=1
            )
            
            # Update layout
            fig.update_layout(
                height=600,
                showlegend=True,
                template='plotly_dark'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display raw data
            st.write("Income Statement Data (in millions)")
            st.dataframe(income_stmt / 1e6)
        else:
            st.info("Income statement data not available.")
            
    except Exception as e:
        st.error(f"Error displaying income statement: {str(e)}")

def show_balance_sheet(ticker_symbol, info):
    """Display balance sheet analysis."""
    try:
        st.subheader("Balance Sheet Analysis")
        
        # Get balance sheet data
        stock = yf.Ticker(ticker_symbol)
        balance_sheet = stock.balance_sheet
        
        if balance_sheet.empty:
            st.warning("No balance sheet data available for this stock.")
            return
        
        # Create columns for key metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Assets & Liabilities Overview**")
            
            # Get the most recent balance sheet data
            latest_data = balance_sheet.iloc[:, 0]
            
            # Try different keys for total assets and liabilities
            total_assets = latest_data.get('Total Assets', 
                                         latest_data.get('TotalAssets', 
                                         info.get('totalAssets', 0)))
            
            # Try different variations of liability keys
            total_liab = latest_data.get('Total Liab', 
                                       latest_data.get('TotalLiab',
                                       latest_data.get('Total Liabilities',
                                       latest_data.get('TotalLiabilities',
                                       info.get('totalLiab', 0)))))
            
            # Calculate shareholders' equity
            total_equity = total_assets - total_liab if total_assets and total_liab else None
            
            # Format values in billions/millions for better readability
            def format_value(value):
                if value is None or value == 0:
                    return "N/A"
                elif abs(value) >= 1e9:
                    return f"${value/1e9:.2f}B"
                else:
                    return f"${value/1e6:.2f}M"
            
            # Display key metrics
            metrics = {
                "Total Assets": total_assets,
                "Total Liabilities": total_liab,
                "Shareholders' Equity": total_equity
            }
            
            for metric, value in metrics.items():
                st.metric(
                    label=metric,
                    value=format_value(value)
                )
            
            # Calculate and display financial health ratios
            if total_assets and total_liab and total_equity and all(v != 0 for v in [total_assets, total_liab, total_equity]):
                st.write("\n**Financial Health Ratios**")
                
                # Current ratio
                current_assets = latest_data.get('Total Current Assets',
                                               latest_data.get('TotalCurrentAssets', 0))
                current_liab = latest_data.get('Total Current Liabilities',
                                             latest_data.get('TotalCurrentLiabilities', 0))
                
                if current_assets and current_liab and current_liab != 0:
                    current_ratio = current_assets / current_liab
                    st.write(f"Current Ratio: {current_ratio:.2f}")
                    
                    # Add interpretation
                    if current_ratio > 2:
                        st.write("✅ Strong liquidity position")
                    elif current_ratio > 1:
                        st.write("📊 Adequate liquidity")
                    else:
                        st.write("⚠️ Potential liquidity concerns")
                
                # Debt-to-Equity ratio
                if total_liab and total_equity and total_equity != 0:
                    de_ratio = total_liab / total_equity
                    st.write(f"Debt-to-Equity Ratio: {de_ratio:.2f}")
                    
                    # Add interpretation
                    if de_ratio < 1:
                        st.write("✅ Conservative financial structure")
                    elif de_ratio < 2:
                        st.write("📊 Moderate leverage")
                    else:
                        st.write("⚠️ High leverage")
        
        with col2:
            st.write("**Balance Sheet Composition**")
            
            # Create a pie chart for assets composition
            fig_assets = go.Figure()
            
            # Try to get detailed asset breakdown
            current_assets = latest_data.get('Total Current Assets',
                                           latest_data.get('TotalCurrentAssets', 0))
            non_current_assets = total_assets - current_assets if total_assets and current_assets else 0
            
            if current_assets or non_current_assets:
                fig_assets.add_trace(go.Pie(
                    labels=['Current Assets', 'Non-current Assets'],
                    values=[current_assets, non_current_assets],
                    name="Assets"
                ))
                
                fig_assets.update_layout(
                    title="Assets Breakdown",
                    template='plotly_dark',
                    showlegend=True
                )
                
                st.plotly_chart(fig_assets, use_container_width=True)
            
            # Create a pie chart for liabilities and equity
            fig_liab = go.Figure()
            
            if total_liab and total_equity:
                fig_liab.add_trace(go.Pie(
                    labels=['Total Liabilities', "Shareholders' Equity"],
                    values=[total_liab, total_equity],
                    name="Liabilities & Equity"
                ))
                
                fig_liab.update_layout(
                    title="Liabilities & Equity Breakdown",
                    template='plotly_dark',
                    showlegend=True
                )
                
                st.plotly_chart(fig_liab, use_container_width=True)
        
        # Display historical balance sheet data
        st.write("\n**Historical Balance Sheet Data**")
        
        # Format the balance sheet data
        formatted_bs = balance_sheet.copy()
        # Convert to millions for better readability
        formatted_bs = formatted_bs / 1e6
        
        # Format column headers to show years only
        formatted_bs.columns = formatted_bs.columns.strftime('%Y')
        
        # Round values to 2 decimal places
        formatted_bs = formatted_bs.round(2)
        
        # Add unit note
        st.write("*All values in millions USD*")
        
        # Display the formatted balance sheet
        st.dataframe(formatted_bs, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error displaying balance sheet: {str(e)}")
        logger.error(f"Error in show_balance_sheet: {str(e)}\n{traceback.format_exc()}")

def show_cash_flow(stock):
    """Display cash flow analysis."""
    
    st.subheader("Cash Flow Analysis")
    
    try:
        # Get cash flow data
        cash_flow = stock.cashflow
        
        if not cash_flow.empty:
            # Calculate free cash flow
            if 'Operating Cash Flow' in cash_flow.index and 'Capital Expenditures' in cash_flow.index:
                free_cash_flow = cash_flow.loc['Operating Cash Flow'] - abs(cash_flow.loc['Capital Expenditures'])
                
                # Create visualization
                fig = go.Figure()
                
                # Add traces for different cash flow components
                fig.add_trace(
                    go.Bar(
                        x=cash_flow.columns,
                        y=cash_flow.loc['Operating Cash Flow'],
                        name='Operating Cash Flow',
                        marker_color='lightgreen'
                    )
                )
                
                fig.add_trace(
                    go.Bar(
                        x=cash_flow.columns,
                        y=-abs(cash_flow.loc['Capital Expenditures']),
                        name='Capital Expenditures',
                        marker_color='salmon'
                    )
                )
                
                fig.add_trace(
                    go.Bar(
                        x=cash_flow.columns,
                        y=free_cash_flow,
                        name='Free Cash Flow',
                        marker_color='lightblue'
                    )
                )
                
                # Update layout
                fig.update_layout(
                    title='Cash Flow Components Over Time',
                    barmode='group',
                    height=400,
                    template='plotly_dark'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate and display FCF margin
                if 'Total Revenue' in stock.financials.index:
                    fcf_margin = (free_cash_flow / stock.financials.loc['Total Revenue']) * 100
                    st.write("**Free Cash Flow Margin**")
                    st.line_chart(fcf_margin)
            
            # Display raw data
            st.write("Cash Flow Data (in millions)")
            st.dataframe(cash_flow / 1e6)
        else:
            st.info("Cash flow data not available.")
            
    except Exception as e:
        st.error(f"Error displaying cash flow: {str(e)}")

def show_financial_ratios(info):
    """Display key financial ratios."""
    
    st.subheader("Financial Ratios")
    
    # Create columns for different ratio categories
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Valuation Ratios**")
        metrics = {
            "P/E Ratio (TTM)": info.get('trailingPE'),
            "Forward P/E": info.get('forwardPE'),
            "PEG Ratio": info.get('pegRatio'),
            "Price/Book": info.get('priceToBook'),
            "Price/Sales": info.get('priceToSalesTrailing12Months')
        }
        
        for name, value in metrics.items():
            if value:
                st.metric(name, f"{value:.2f}")
            else:
                st.metric(name, "N/A")
    
    with col2:
        st.write("**Profitability Ratios**")
        metrics = {
            "Gross Margin": info.get('grossMargins'),
            "Operating Margin": info.get('operatingMargins'),
            "Profit Margin": info.get('profitMargins'),
            "ROE": info.get('returnOnEquity'),
            "ROA": info.get('returnOnAssets')
        }
        
        for name, value in metrics.items():
            if value:
                st.metric(name, f"{value:.2%}")
            else:
                st.metric(name, "N/A")
    
    with col3:
        st.write("**Efficiency Ratios**")
        metrics = {
            "Asset Turnover": info.get('assetTurnover', None),
            "Inventory Turnover": info.get('inventoryTurnover', None),
            "Revenue/Employee": f"${info.get('revenuePerEmployee', 0):,.0f}" if info.get('revenuePerEmployee') else None
        }
        
        for name, value in metrics.items():
            if value:
                st.metric(name, value)
            else:
                st.metric(name, "N/A") 