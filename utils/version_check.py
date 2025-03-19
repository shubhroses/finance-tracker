import streamlit as st
import pkg_resources

def check_yfinance_version():
    """Check the installed version of yfinance and warn if outdated."""
    try:
        yfinance_version = pkg_resources.get_distribution("yfinance").version
        st.sidebar.text(f"yfinance version: {yfinance_version}")
        
        # Warning for older versions known to have datetime issues
        if yfinance_version < "0.2.0":
            st.sidebar.warning("You're using an older version of yfinance which may have compatibility issues. Consider upgrading with: pip install yfinance --upgrade --no-cache-dir")
    except:
        st.sidebar.text("Could not detect yfinance version") 