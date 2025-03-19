import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import logging
import traceback
import requests
from bs4 import BeautifulSoup
import json
import time
from .utils import get_stock_news, get_session
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('news_sentiment')

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_yahoo_finance_news(ticker_symbol, max_retries=5, retry_delay=2):
    """Get news from Yahoo Finance with retry logic and caching."""
    for attempt in range(max_retries):
        try:
            # Add delay between retries
            if attempt > 0:
                delay = (retry_delay * (2 ** attempt)) + (random.random() * 0.5)
                logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s delay")
                time.sleep(delay)
            
            urls = [
                f"https://finance.yahoo.com/quote/{ticker_symbol}/news",
                f"https://finance.yahoo.com/quote/{ticker_symbol}"
            ]
            
            session = get_session()  # Use the shared session from utils.py
            news_items = []
            
            for url in urls:
                try:
                    response = session.get(url, timeout=10)
                    
                    # Handle rate limiting
                    if response.status_code == 429:
                        logger.warning(f"Rate limited by Yahoo Finance (attempt {attempt + 1}/{max_retries})")
                        continue
                        
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try multiple class patterns for news items
                    news_containers = [
                        soup.find_all('div', {'class': ['Ov(h)', 'IframeSecondaryStream']}),
                        soup.find_all('div', {'data-test': 'story'}),
                        soup.find_all('li', {'class': 'js-stream-content'}),
                        soup.find_all('div', {'class': 'news-link-container'})
                    ]
                    
                    for container in news_containers:
                        if container:
                            for item in container:
                                try:
                                    # Try multiple patterns for title and link
                                    title_elem = (
                                        item.find(['h3', 'a']) or 
                                        item.find('div', {'class': 'text'}) or
                                        item.find('div', {'class': 'headline'})
                                    )
                                    
                                    if not title_elem:
                                        continue
                                    
                                    title = title_elem.text.strip()
                                    link = title_elem.get('href', '')
                                    
                                    if not link and title_elem.parent.name == 'a':
                                        link = title_elem.parent.get('href', '')
                                    
                                    if link and not link.startswith('http'):
                                        link = 'https://finance.yahoo.com' + link
                                    
                                    # Try multiple patterns for publisher and time
                                    meta = (
                                        item.find('div', {'class': ['C(#959595)', 'Fz(11px)']}) or
                                        item.find('div', {'class': 'source'}) or
                                        item.find('div', {'class': 'provider'})
                                    )
                                    
                                    publisher = "Yahoo Finance"
                                    if meta:
                                        publisher_text = meta.text.split('·')[0].strip()
                                        if publisher_text:
                                            publisher = publisher_text
                                    
                                    if title and link:
                                        news_item = {
                                            'title': title,
                                            'link': link,
                                            'publisher': publisher,
                                            'published': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                            'type': 'STORY',
                                            'summary': ''
                                        }
                                        
                                        # Check for duplicates before adding
                                        if not any(x['title'] == title for x in news_items):
                                            news_items.append(news_item)
                                            
                                            if len(news_items) >= 10:
                                                return news_items
                                                
                                except Exception as e:
                                    logger.warning(f"Error parsing Yahoo Finance news item: {str(e)}")
                                    continue
                                    
                    if news_items:
                        break
                        
                except requests.RequestException as e:
                    logger.warning(f"Error fetching from {url}: {str(e)}")
                    continue
            
            if news_items:
                return news_items
                
        except Exception as e:
            logger.error(f"Error in get_yahoo_finance_news (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                return []
    
    return []

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_marketwatch_news(ticker_symbol, limit=10):
    """Fetch news from MarketWatch with caching"""
    try:
        url = f"https://www.marketwatch.com/investing/stock/{ticker_symbol}"
        session = get_session()  # Use the shared session from utils.py
        
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # Find news articles - try multiple selectors
        articles = (
            soup.find_all('div', class_='article__content') or
            soup.find_all('div', class_='element element--article') or
            soup.find_all('div', class_='story__content') or
            soup.find_all('div', class_='article__wrap')
        )
        
        for article in articles[:limit]:
            try:
                # Try multiple patterns for title
                title_elem = (
                    article.find('a', class_='link') or
                    article.find('h3', class_='article__headline') or
                    article.find('a', class_='headline__link') or
                    article.find('h3', class_='headline')
                )
                
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                link = title_elem.get('href', '')
                
                if not link.startswith('http'):
                    link = f"https://www.marketwatch.com{link}"
                
                # Try multiple patterns for timestamp
                timestamp_elem = (
                    article.find('span', class_='article__timestamp') or
                    article.find('div', class_='article__details') or
                    article.find('time', class_='timestamp') or
                    article.find('div', class_='timestamp')
                )
                
                # Default to current time if no timestamp found
                timestamp = datetime.now()
                
                if timestamp_elem:
                    timestamp_text = timestamp_elem.text.strip().lower()
                    try:
                        # Handle relative time formats
                        if 'ago' in timestamp_text:
                            value = int(''.join(filter(str.isdigit, timestamp_text)))
                            if 'minute' in timestamp_text or 'min' in timestamp_text:
                                timestamp = datetime.now() - timedelta(minutes=value)
                            elif 'hour' in timestamp_text or 'hr' in timestamp_text:
                                timestamp = datetime.now() - timedelta(hours=value)
                            elif 'day' in timestamp_text:
                                timestamp = datetime.now() - timedelta(days=value)
                            elif 'week' in timestamp_text:
                                timestamp = datetime.now() - timedelta(weeks=value)
                            elif 'month' in timestamp_text:
                                timestamp = datetime.now() - timedelta(days=value * 30)
                        # Handle absolute time formats
                        elif ':' in timestamp_text:  # Today's time
                            time_parts = timestamp_text.split(':')
                            if len(time_parts) == 2:
                                hour, minute = map(int, time_parts)
                                timestamp = datetime.now().replace(hour=hour, minute=minute)
                        elif '/' in timestamp_text:  # Date format
                            timestamp = datetime.strptime(timestamp_text, '%m/%d/%Y')
                    except Exception as e:
                        logger.warning(f"Error parsing timestamp '{timestamp_text}': {str(e)}")
                
                # Try to get summary
                summary_elem = (
                    article.find('p', class_='article__summary') or
                    article.find('div', class_='article__description') or
                    article.find('p', class_='description')
                )
                summary = summary_elem.text.strip() if summary_elem else ""
                
                news_item = {
                    'title': title,
                    'link': link,
                    'publisher': 'MarketWatch',
                    'published': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'summary': summary,
                    'type': 'article'
                }
                
                if validate_news_item(news_item):
                    news_items.append(news_item)
                    
            except Exception as e:
                logger.error(f"Error parsing MarketWatch article: {str(e)}")
                continue
        
        if news_items:
            # Sort news items by timestamp, most recent first
            news_items.sort(key=lambda x: datetime.strptime(x['published'], '%Y-%m-%d %H:%M:%S'), reverse=True)
            logger.info(f"Successfully fetched {len(news_items)} news items from MarketWatch")
            return news_items
        else:
            logger.warning("No valid news items found from MarketWatch")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching MarketWatch news: {str(e)}")
        return None

def get_seeking_alpha_news(ticker_symbol):
    """Get news from Seeking Alpha."""
    try:
        url = f"https://seekingalpha.com/symbol/{ticker_symbol}/news"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # Try multiple patterns for news containers
        news_containers = [
            soup.find_all('div', {'data-test-id': 'post-list-item'}),
            soup.find_all('article'),
            soup.find_all('div', {'class': ['news-item', 'media-preview-content']})
        ]
        
        for container in news_containers:
            if container:
                for item in container:
                    try:
                        # Find title and link
                        title_elem = (
                            item.find('a', {'data-test-id': 'post-list-item-title'}) or
                            item.find(['h3', 'h4']) or
                            item.find('a', {'class': 'title'})
                        )
                        
                        if not title_elem:
                            continue
                            
                        title = title_elem.text.strip()
                        link = title_elem.get('href', '')
                        
                        if link and not link.startswith('http'):
                            link = 'https://seekingalpha.com' + link
                        
                        # Create news item
                        if title and link:
                            news_item = {
                                'title': title,
                                'link': link,
                                'publisher': 'Seeking Alpha',
                                'providerPublishTime': int(datetime.now().timestamp()),
                                'type': 'STORY',
                                'summary': ''
                            }
                            news_items.append(news_item)
                            
                            if len(news_items) >= 10:
                                return news_items
                                
                    except Exception as e:
                        logger.warning(f"Error parsing Seeking Alpha news item: {str(e)}")
                        continue
        
        return news_items
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching Seeking Alpha news: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error fetching Seeking Alpha news: {str(e)}")
        return []

def validate_news_item(item):
    """Validate if a news item has all required fields"""
    required_fields = ['title', 'link', 'publisher']
    
    if not isinstance(item, dict):
        return False
        
    for field in required_fields:
        if field not in item or not item[field]:
            return False
            
    # Ensure we have either providerPublishTime or published
    if 'providerPublishTime' not in item and 'published' not in item:
        item['published'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
    return True

def format_date(timestamp):
    """Format timestamp to readable date"""
    try:
        if isinstance(timestamp, (int, float)):
            # Check if timestamp is in milliseconds
            if timestamp > 1e11:
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(timestamp, str):
            # Try parsing the string date
            try:
                return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                return timestamp
        return timestamp
    except Exception as e:
        logger.error(f"Error formatting date: {str(e)}")
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def show_news_sentiment(ticker_symbol):
    """Display news and sentiment analysis for a given stock"""
    st.header("News & Sentiment Analysis")
    
    try:
        with st.spinner('Fetching news articles...'):
            # First try to get news from Yahoo Finance with caching
            news_items = get_stock_news(ticker_symbol)
            valid_news = []
            
            if news_items:
                logger.info(f"Found {len(news_items)} news items from yfinance")
                
                for item in news_items:
                    # Log the item structure for debugging
                    logger.info(f"Processing news item with keys: {list(item.keys())}")
                    
                    # Try to extract title from different fields
                    title = None
                    if isinstance(item, dict):
                        # Try multiple fields for title
                        for field in ['title', 'headline', 'Title', 'Headline']:
                            if field in item and item[field]:
                                title = item[field]
                                break
                        
                        # If no title found, try using the first sentence of description/summary
                        if not title:
                            for field in ['description', 'summary', 'Description', 'Summary']:
                                if field in item and item[field]:
                                    title = item[field].split('.')[0].strip()
                                    break
                    
                    # If we found a title, create a valid news item
                    if title:
                        # Try multiple fields for link/url
                        link = None
                        for field in ['link', 'url', 'Link', 'URL']:
                            if field in item and item[field]:
                                link = item[field]
                                break
                        
                        if not link:
                            logger.warning(f"No link found for news item with title: {title}")
                            continue
                        
                        # Create the news item with all available fields
                        valid_item = {
                            'title': title,
                            'link': link,
                            'publisher': item.get('publisher', 'Yahoo Finance'),
                            'published': format_date(item.get('providerPublishTime', datetime.now().timestamp())),
                            'summary': item.get('description', item.get('summary', '')),
                            'type': item.get('type', 'STORY')
                        }
                        
                        if validate_news_item(valid_item):
                            valid_news.append(valid_item)
                            logger.info(f"Added valid news item: {valid_item['title']}")
                        else:
                            logger.warning(f"Invalid news item: {valid_item}")
                    else:
                        logger.warning("Could not find title in news item")
            
            # If no valid news from Yahoo Finance, try MarketWatch
            if not valid_news:
                logger.info("No valid news items from Yahoo Finance, trying MarketWatch")
                marketwatch_news = get_marketwatch_news(ticker_symbol)
                
                if marketwatch_news:
                    valid_news.extend(marketwatch_news)
                    logger.info(f"Added {len(marketwatch_news)} valid MarketWatch articles")
            
            if valid_news:
                # Sort news by date if available
                try:
                    valid_news.sort(key=lambda x: datetime.strptime(x['published'], '%Y-%m-%d %H:%M:%S'), reverse=True)
                except Exception as e:
                    logger.warning(f"Error sorting news by date: {str(e)}")
                
                # Display news articles in a modern card layout
                for article in valid_news:
                    with st.container():
                        # Create a card-like container using Streamlit's native components
                        col1 = st.container()
                        with col1:
                            # Display title with publisher badge
                            st.markdown(f"### {article['title']} {get_publisher_badge(article['publisher'])}")
                            
                            # Display metadata (date and publisher)
                            st.markdown(
                                f"📅 {article.get('published', 'No date available')} | "
                                f"📰 {article['publisher']}"
                            )
                            
                            # Display summary if available
                            if article.get('summary'):
                                st.markdown(article['summary'])
                            
                            # Use markdown for the link instead of a button
                            st.markdown(f"[Read More →]({article['link']})")
                        
                        # Add some spacing between articles
                        st.markdown("---")
            else:
                st.warning(
                    """No news articles could be retrieved at this moment. This may be due to:
                    - Rate limiting from our data sources
                    - Temporary service disruption
                    - Network connectivity issues
                    
                    Please try again in a few minutes. In the meantime, you can:
                    - Check the stock's technical analysis
                    - Review financial metrics
                    - Explore the company overview"""
                )
                
    except Exception as e:
        logger.error(f"Error in show_news_sentiment: {str(e)}\n{traceback.format_exc()}")
        st.error(
            """Unable to fetch news articles. This could be due to:
            - Service disruption
            - Network connectivity issues
            - Rate limiting
            
            Please try again later."""
        )

def get_publisher_badge(publisher):
    """Return a colored badge based on the publisher's reliability"""
    if publisher.lower() in ['reuters', 'bloomberg', 'cnbc', 'financial times']:
        return "🟢"  # High reliability
    elif publisher.lower() in ['yahoo finance', 'marketwatch', 'seeking alpha']:
        return "🟡"  # Standard reliability
    else:
        return "⚪"  # Unknown reliability

def show_recent_news(news):
    """Display recent news articles."""
    
    st.subheader("Recent News")
    
    try:
        if not news:
            st.warning("No recent news articles available.")
            return
        
        # Display news count
        st.write(f"Found {len(news)} recent news articles")
        
        for article in news:
            # Validate timestamp
            timestamp = article.get('providerPublishTime', 0)
            if timestamp <= 946684800:  # Before January 1, 2000
                continue
                
            # Format publish time
            publish_time = datetime.fromtimestamp(timestamp)
            
            # Create an expander for each article
            with st.expander(
                f"{article.get('title', '[No Title]')} - {article.get('publisher', 'Unknown Publisher')} "
                f"({publish_time.strftime('%Y-%m-%d %H:%M')})"
            ):
                try:
                    # Display article details
                    if article.get('link'):
                        st.markdown(f"[Read Full Article]({article['link']})")
                    
                    if article.get('summary'):
                        st.write("**Summary:**")
                        st.write(article['summary'])
                    else:
                        st.write("*No summary available*")
                    
                    # Display additional metadata in columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if article.get('type'):
                            st.write(f"**Type:** {article['type']}")
                        if article.get('relatedTickers'):
                            st.write(f"**Related Tickers:** {', '.join(article['relatedTickers'])}")
                    
                    with col2:
                        if article.get('publisher'):
                            st.write(f"**Publisher:** {article['publisher']}")
                        st.write(f"**Published:** {publish_time.strftime('%Y-%m-%d %H:%M')}")
                        
                        # Add source reliability indicator if available
                        if article.get('publisher') in ['Reuters', 'Bloomberg', 'CNBC', 'Financial Times']:
                            st.write("**Source Quality:** 🟢 High Reliability")
                        elif article.get('publisher'):
                            st.write("**Source Quality:** 🟡 Standard Source")
                
                except Exception as e:
                    logger.error(f"Error displaying article: {str(e)}")
                    st.error("Error displaying this article")
                    continue
    
    except Exception as e:
        logger.error(f"Error in show_recent_news: {str(e)}\n{traceback.format_exc()}")
        st.error("Error displaying news articles")

def show_sentiment_analysis(news, ticker_symbol):
    """Display sentiment analysis of news articles."""
    
    st.subheader("Sentiment Analysis")
    
    try:
        # Prepare data for sentiment analysis
        sentiments = []
        dates = []
        
        for article in news:
            sentiment = analyze_article_sentiment(article)
            sentiments.append(sentiment)
            dates.append(datetime.fromtimestamp(article.get('providerPublishTime', 0)))
        
        if not sentiments:
            st.warning("No articles available for sentiment analysis")
            return
        
        # Create sentiment timeline
        fig = go.Figure()
        
        # Add sentiment score line
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=sentiments,
                mode='lines+markers',
                name='Sentiment Score',
                line=dict(color='lightblue'),
                marker=dict(
                    size=8,
                    color=sentiments,
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title='Sentiment')
                )
            )
        )
        
        # Update layout
        fig.update_layout(
            title=f'News Sentiment Timeline for {ticker_symbol}',
            xaxis_title='Date',
            yaxis_title='Sentiment Score',
            template='plotly_dark',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display sentiment statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_sentiment = np.mean(sentiments)
            st.metric(
                "Average Sentiment",
                f"{avg_sentiment:.2f}",
                delta=None,
                delta_color="normal"
            )
        
        with col2:
            positive_ratio = sum(1 for s in sentiments if s > 0) / len(sentiments)
            st.metric(
                "Positive News Ratio",
                f"{positive_ratio:.1%}",
                delta=None,
                delta_color="normal"
            )
        
        with col3:
            sentiment_volatility = np.std(sentiments)
            st.metric(
                "Sentiment Volatility",
                f"{sentiment_volatility:.2f}",
                delta=None,
                delta_color="normal"
            )
        
        # Display sentiment distribution
        fig_dist = go.Figure()
        
        fig_dist.add_trace(
            go.Histogram(
                x=sentiments,
                nbinsx=20,
                name='Sentiment Distribution',
                marker_color='lightblue'
            )
        )
        
        fig_dist.update_layout(
            title='Distribution of News Sentiment',
            xaxis_title='Sentiment Score',
            yaxis_title='Number of Articles',
            template='plotly_dark',
            height=300
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error in show_sentiment_analysis: {str(e)}\n{traceback.format_exc()}")
        st.error("Error performing sentiment analysis")

def show_news_impact(news, hist, ticker_symbol):
    """Display analysis of news impact on stock price."""
    
    st.subheader("News Impact Analysis")
    
    try:
        if hist.empty:
            st.warning("No historical price data available for impact analysis")
            return
        
        # Create figure with price and news events
        fig = go.Figure()
        
        # Add price line
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['Close'],
                name='Stock Price',
                line=dict(color='lightblue', width=2)
            )
        )
        
        # Add markers for news events
        news_dates = []
        news_prices = []
        news_texts = []
        
        for article in news:
            date = datetime.fromtimestamp(article.get('providerPublishTime', 0))
            if date in hist.index:
                news_dates.append(date)
                news_prices.append(hist.loc[date, 'Close'])
                news_texts.append(article.get('title', 'No title'))
        
        if news_dates:
            fig.add_trace(
                go.Scatter(
                    x=news_dates,
                    y=news_prices,
                    mode='markers',
                    name='News Events',
                    marker=dict(
                        size=10,
                        symbol='star',
                        color='yellow'
                    ),
                    text=news_texts,
                    hovertemplate=
                    '<b>Date</b>: %{x}<br>' +
                    '<b>Price</b>: $%{y:.2f}<br>' +
                    '<b>News</b>: %{text}<br>'
                )
            )
        
        # Update layout
        fig.update_layout(
            title=f'Stock Price and News Events for {ticker_symbol}',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            template='plotly_dark',
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Analyze price movements following news
        if news_dates:
            st.write("**Significant Price Moves Following News:**")
            
            for i, date in enumerate(news_dates):
                if date in hist.index:
                    # Look at price change in next 2 days
                    start_price = hist.loc[date, 'Close']
                    future_prices = hist.loc[date:].head(3)['Close']
                    
                    if len(future_prices) > 1:
                        max_change = ((future_prices.max() - start_price) / start_price) * 100
                        min_change = ((future_prices.min() - start_price) / start_price) * 100
                        
                        if abs(max_change) > 1 or abs(min_change) > 1:  # Only show significant moves (>1%)
                            st.write(f"After news on {date.strftime('%Y-%m-%d')}:")
                            st.write(f"- Maximum price change: {max_change:+.2f}%")
                            st.write(f"- Minimum price change: {min_change:+.2f}%")
                            st.write(f"- News: {news_texts[i]}")
                            st.write("---")
        
    except Exception as e:
        logger.error(f"Error in show_news_impact: {str(e)}\n{traceback.format_exc()}")
        st.error("Error analyzing news impact")

def analyze_article_sentiment(article):
    """Calculate sentiment score for a news article."""
    
    try:
        # Initialize sentiment score
        sentiment_score = 0
        
        # Get text to analyze
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        
        # Define sentiment words (simplified version)
        positive_words = {
            'buy', 'bullish', 'upward', 'growth', 'profit', 'positive', 'gain', 'surge',
            'jump', 'rise', 'rising', 'higher', 'increase', 'increased', 'strong',
            'strength', 'opportunity', 'opportunities', 'success', 'successful',
            'improve', 'improved', 'improving', 'beat', 'beats', 'beating'
        }
        
        negative_words = {
            'sell', 'bearish', 'downward', 'decline', 'loss', 'negative', 'drop',
            'plunge', 'fall', 'falling', 'lower', 'decrease', 'decreased', 'weak',
            'weakness', 'risk', 'risks', 'fail', 'failed', 'failing', 'miss',
            'misses', 'missing', 'down', 'debt', 'investigation'
        }
        
        # Count sentiment words in title (weighted more heavily)
        for word in title.split():
            if word in positive_words:
                sentiment_score += 0.5
            elif word in negative_words:
                sentiment_score -= 0.5
        
        # Count sentiment words in summary
        for word in summary.split():
            if word in positive_words:
                sentiment_score += 0.25
            elif word in negative_words:
                sentiment_score -= 0.25
        
        # Normalize score to range [-1, 1]
        max_possible_score = (len(title.split()) + len(summary.split())) * 0.5
        if max_possible_score > 0:
            sentiment_score = sentiment_score / max_possible_score
        
        return sentiment_score
    
    except Exception as e:
        logger.error(f"Error in analyze_article_sentiment: {str(e)}\n{traceback.format_exc()}")
        return 0  # Return neutral sentiment on error 