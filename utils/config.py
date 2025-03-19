import streamlit as st

def setup_page_config():
    """Set up the Streamlit page configuration."""
    st.set_page_config(
        page_title="Financial Visualizer",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    ) 