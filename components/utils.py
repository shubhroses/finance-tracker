import streamlit as st
import time
import random
from functools import wraps
import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global session for rate limiting
_session = None
_last_request_time = datetime.min
_min_request_interval = 2.0  # Minimum seconds between requests

def get_session():
    """Get a session with retry strategy"""
    global _session
    if _session is None:
        _session = requests.Session()
        
        # Configure retry strategy
        retries = Retry(
            total=5,  # Total number of retries
            backoff_factor=2,  # Will wait: {backoff_factor} * (2 ** ({number_of_total_retries} - 1))
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retries)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
        
        # Set default headers
        _session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    return _session

def rate_limit_request():
    """Ensure minimum delay between requests"""
    global _last_request_time
    current_time = datetime.now()
    time_since_last_request = (current_time - _last_request_time).total_seconds()
    
    if time_since_last_request < _min_request_interval:
        sleep_time = _min_request_interval - time_since_last_request
        time.sleep(sleep_time)
    
    _last_request_time = datetime.now()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_info(ticker_symbol, max_retries=5, initial_delay=2):
    """Get stock information with improved rate limiting and caching"""
    for attempt in range(max_retries):
        try:
            # Apply rate limiting
            rate_limit_request()
            
            # Add jitter to prevent synchronized retries
            delay = (initial_delay * (2 ** attempt)) + (random.random() * 0.5)
            
            if attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s delay")
                time.sleep(delay)
            
            # Use custom session
            stock = yf.Ticker(ticker_symbol)
            stock._session = get_session()
            info = stock.info
            
            if info:
                return info
                
        except Exception as e:
            if "429" in str(e):
                logger.warning(f"Rate limited by Yahoo Finance (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    logger.error("Max retries reached for Yahoo Finance API")
                    return None
            else:
                logger.error(f"Error fetching stock info: {str(e)}")
                return None
    
    return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_news(ticker_symbol, max_retries=5, initial_delay=2):
    """Get stock news with improved rate limiting and caching"""
    for attempt in range(max_retries):
        try:
            # Apply rate limiting
            rate_limit_request()
            
            # Add jitter to prevent synchronized retries
            delay = (initial_delay * (2 ** attempt)) + (random.random() * 0.5)
            
            if attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s delay")
                time.sleep(delay)
            
            # Use custom session
            stock = yf.Ticker(ticker_symbol)
            stock._session = get_session()
            
            try:
                # Try to get news directly from the news property
                news = stock.news
                if news:
                    logger.info(f"Successfully fetched {len(news)} news items from yfinance")
                    # Log the structure of the first news item for debugging
                    if news:
                        logger.info(f"Sample news item structure: {list(news[0].keys())}")
                    return news
            except Exception as e:
                logger.warning(f"Error getting news from stock.news: {str(e)}")
            
            # If news property fails, try getting it from fast_info
            try:
                news = stock.fast_info
                if hasattr(news, 'news') and news.news:
                    logger.info(f"Successfully fetched news from fast_info")
                    return news.news
            except Exception as e:
                logger.warning(f"Error getting news from fast_info: {str(e)}")
            
            # If both methods fail, try scraping the website directly
            try:
                session = get_session()
                url = f"https://finance.yahoo.com/quote/{ticker_symbol}/news"
                response = session.get(url, timeout=10)
                
                if response.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    news_items = []
                    articles = soup.find_all(['h3', 'a'], class_=['Mb(5px)'])
                    
                    for article in articles:
                        if article.text and article.get('href'):
                            news_items.append({
                                'title': article.text.strip(),
                                'link': f"https://finance.yahoo.com{article.get('href')}",
                                'publisher': 'Yahoo Finance',
                                'providerPublishTime': int(datetime.now().timestamp()),
                                'type': 'STORY'
                            })
                    
                    if news_items:
                        logger.info(f"Successfully scraped {len(news_items)} news items from Yahoo Finance website")
                        return news_items
            except Exception as e:
                logger.warning(f"Error scraping Yahoo Finance website: {str(e)}")
            
            # If we get here, all methods failed for this attempt
            if attempt == max_retries - 1:
                logger.error("All methods failed to fetch news")
                return None
                
        except Exception as e:
            if "429" in str(e):
                logger.warning(f"Rate limited by Yahoo Finance (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    logger.error("Max retries reached for Yahoo Finance API")
                    return None
            else:
                logger.error(f"Error fetching stock news: {str(e)}")
                return None
    
    return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_history(ticker_symbol, period="1y", interval="1d"):
    """Get stock price history with rate limiting and caching"""
    try:
        # Apply rate limiting
        rate_limit_request()
        
        # Use custom session
        stock = yf.Ticker(ticker_symbol)
        stock._session = get_session()
        df = stock.history(period=period, interval=interval)
        
        if df.empty:
            return None
            
        return df
        
    except Exception as e:
        logger.error(f"Error fetching stock history: {str(e)}")
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_financials(ticker_symbol):
    """Get stock financial data with rate limiting and caching"""
    try:
        # Apply rate limiting
        rate_limit_request()
        
        # Use custom session
        stock = yf.Ticker(ticker_symbol)
        stock._session = get_session()
        
        # Get financial statements with more detailed error handling
        try:
            income_stmt = stock.income_stmt
            if income_stmt is None or income_stmt.empty:
                logger.warning(f"No income statement data available for {ticker_symbol}")
        except Exception as e:
            logger.error(f"Error fetching income statement for {ticker_symbol}: {str(e)}")
            income_stmt = None
            
        try:
            balance_sheet = stock.balance_sheet
            if balance_sheet is None or balance_sheet.empty:
                logger.warning(f"No balance sheet data available for {ticker_symbol}")
        except Exception as e:
            logger.error(f"Error fetching balance sheet for {ticker_symbol}: {str(e)}")
            balance_sheet = None
            
        try:
            cash_flow = stock.cash_flow
            if cash_flow is None or cash_flow.empty:
                logger.warning(f"No cash flow data available for {ticker_symbol}")
        except Exception as e:
            logger.error(f"Error fetching cash flow for {ticker_symbol}: {str(e)}")
            cash_flow = None
        
        # Validate and clean financial statements
        def clean_statement(df):
            if df is None or df.empty:
                return None
                
            try:
                # Convert all values to numeric, coercing errors to NaN
                df = df.apply(pd.to_numeric, errors='coerce')
                
                # Drop any columns where all values are NaN
                df = df.dropna(axis=1, how='all')
                
                # Drop any rows where all values are NaN
                df = df.dropna(how='all')
                
                # Sort columns by date (most recent first)
                df = df.sort_index(axis=1, ascending=False)
                
                return df
            except Exception as e:
                logger.error(f"Error cleaning financial statement: {str(e)}")
                return None
        
        income_stmt = clean_statement(income_stmt)
        balance_sheet = clean_statement(balance_sheet)
        cash_flow = clean_statement(cash_flow)
        
        if all(stmt is None for stmt in [income_stmt, balance_sheet, cash_flow]):
            logger.error(f"No valid financial data found for {ticker_symbol}")
            return None
            
        return income_stmt, balance_sheet, cash_flow
        
    except Exception as e:
        logger.error(f"Error fetching financial data for {ticker_symbol}: {str(e)}")
        return None 