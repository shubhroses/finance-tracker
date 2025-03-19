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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('news_sentiment')

def get_yahoo_finance_news(ticker_symbol):
    """Get news from Yahoo Finance."""
    try:
        # Try multiple URL patterns
        urls = [
            f"https://finance.yahoo.com/quote/{ticker_symbol}/news",
            f"https://finance.yahoo.com/quote/{ticker_symbol}"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        news_items = []
        
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
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
                                        'providerPublishTime': int(datetime.now().timestamp()),
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
        
        return news_items
        
    except Exception as e:
        logger.error(f"Error in get_yahoo_finance_news: {str(e)}")
        return []

def get_marketwatch_news(ticker_symbol):
    """Get news from MarketWatch."""
    try:
        # Use the latest news URL
        url = f"https://www.marketwatch.com/investing/stock/{ticker_symbol}/news"
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
        
        # Look for news items in the article list
        news_list = soup.find_all('div', {'class': ['article__content', 'story__content']})
        
        for item in news_list:
            try:
                # Find title and link
                title_elem = item.find('a', {'class': ['link', 'headline']})
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                link = title_elem.get('href', '')
                if not link.startswith('http'):
                    link = 'https://www.marketwatch.com' + link
                
                # Find time element
                time_elem = item.find(['time', 'span'], {'class': ['article__timestamp', 'timestamp']})
                
                # Create news item
                if title and link:
                    news_item = {
                        'title': title,
                        'link': link,
                        'publisher': 'MarketWatch',
                        'providerPublishTime': int(datetime.now().timestamp()),
                        'type': 'STORY',
                        'summary': ''
                    }
                    news_items.append(news_item)
                    
                    if len(news_items) >= 10:  # Limit to 10 most recent news items
                        break
                        
            except Exception as e:
                logger.warning(f"Error parsing MarketWatch news item: {str(e)}")
                continue
        
        return news_items
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching MarketWatch news: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error fetching MarketWatch news: {str(e)}")
        return []

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

def show_news_sentiment(ticker_symbol):
    """Display news and sentiment analysis for a given stock."""
    
    st.header('News & Sentiment Analysis')
    
    try:
        # Show loading message
        with st.spinner('Fetching news from multiple sources...'):
            # Initialize news list
            all_news = []
            
            # Try yfinance first
            try:
                stock = yf.Ticker(ticker_symbol)
                yf_news = stock.news
                
                if yf_news:
                    logger.info(f"Found {len(yf_news)} news items from yfinance")
                    
                    # Process yfinance news items
                    for article in yf_news:
                        try:
                            # Ensure required fields exist
                            if not article.get('title'):
                                logger.warning("Skipping article without title")
                                continue
                                
                            # Convert unix timestamp to datetime if needed
                            timestamp = article.get('providerPublishTime', 0)
                            if timestamp == 0 and article.get('publishedAt'):
                                try:
                                    timestamp = int(datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').timestamp())
                                except Exception as e:
                                    logger.warning(f"Error parsing publishedAt date: {e}")
                                    timestamp = int(datetime.now().timestamp())
                            
                            # Create standardized news item
                            news_item = {
                                'title': article.get('title'),
                                'link': article.get('link'),
                                'publisher': article.get('publisher', 'Yahoo Finance'),
                                'providerPublishTime': timestamp,
                                'type': article.get('type', 'STORY'),
                                'summary': article.get('summary', '')
                            }
                            
                            all_news.append(news_item)
                            logger.debug(f"Processed yfinance article: {news_item['title']}")
                            
                        except Exception as e:
                            logger.warning(f"Error processing yfinance article: {str(e)}")
                            continue
                    
                    logger.info(f"Successfully processed {len(all_news)} yfinance news items")
                else:
                    logger.warning("No news items found from yfinance")
            except Exception as e:
                logger.warning(f"Error fetching yfinance news: {str(e)}")
            
            # Try other sources if needed
            if len(all_news) < 5:
                logger.info("Insufficient news items, trying alternative sources")
                
                # Try Yahoo Finance web scraping
                try:
                    yahoo_news = get_yahoo_finance_news(ticker_symbol)
                    if yahoo_news:
                        all_news.extend(yahoo_news)
                        logger.info(f"Found {len(yahoo_news)} news items from Yahoo Finance scraping")
                except Exception as e:
                    logger.warning(f"Error fetching Yahoo Finance news: {str(e)}")
                
                # Try MarketWatch
                try:
                    marketwatch_news = get_marketwatch_news(ticker_symbol)
                    if marketwatch_news:
                        all_news.extend(marketwatch_news)
                        logger.info(f"Found {len(marketwatch_news)} news items from MarketWatch")
                except Exception as e:
                    logger.warning(f"Error fetching MarketWatch news: {str(e)}")
                
                # Try Seeking Alpha
                try:
                    seeking_alpha_news = get_seeking_alpha_news(ticker_symbol)
                    if seeking_alpha_news:
                        all_news.extend(seeking_alpha_news)
                        logger.info(f"Found {len(seeking_alpha_news)} news items from Seeking Alpha")
                except Exception as e:
                    logger.warning(f"Error fetching Seeking Alpha news: {str(e)}")
            
            # Validate and deduplicate news
            valid_news = []
            seen_titles = set()
            
            for article in all_news:
                try:
                    # Skip if we've seen this title before
                    title = article.get('title', '').strip()
                    if not title or title in seen_titles:
                        continue
                    
                    # Ensure we have required fields
                    if not article.get('link'):
                        logger.warning(f"Skipping article without link: {title}")
                        continue
                    
                    # Check if article has valid timestamp (after 2000)
                    timestamp = article.get('providerPublishTime', 0)
                    if timestamp <= 946684800:  # January 1, 2000
                        logger.warning(f"Skipping article with invalid timestamp: {title}")
                        continue
                    
                    valid_news.append(article)
                    seen_titles.add(title)
                    logger.debug(f"Added valid article: {title}")
                    
                except Exception as e:
                    logger.warning(f"Error validating article: {str(e)}")
                    continue
            
            logger.info(f"Found {len(valid_news)} valid news articles after validation")
            
            if not valid_news:
                st.warning(f"Unable to retrieve news data for {ticker_symbol}.")
                st.info("This could be due to:")
                st.write("1. Rate limiting from data providers")
                st.write("2. Network connectivity issues")
                st.write("3. Temporary service disruption")
                
                # Show alternative sources with direct news links
                st.write("\nYou can check these sources directly:")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"[Yahoo Finance {ticker_symbol}](https://finance.yahoo.com/quote/{ticker_symbol}/news)")
                    st.markdown(f"[MarketWatch {ticker_symbol}](https://www.marketwatch.com/investing/stock/{ticker_symbol}/news)")
                
                with col2:
                    st.markdown(f"[Reuters {ticker_symbol}](https://www.reuters.com/markets/companies/{ticker_symbol}.O)")
                    st.markdown(f"[Seeking Alpha {ticker_symbol}](https://seekingalpha.com/symbol/{ticker_symbol}/news)")
                
                return
            
            # Sort news by date (most recent first)
            valid_news.sort(key=lambda x: x.get('providerPublishTime', 0), reverse=True)
            
            # Create tabs for different analyses
            news_tabs = st.tabs(['Recent News', 'Sentiment Analysis', 'News Impact'])
            
            with news_tabs[0]:
                show_recent_news(valid_news)
            
            with news_tabs[1]:
                show_sentiment_analysis(valid_news, ticker_symbol)
            
            with news_tabs[2]:
                # Get historical data for the past month
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                hist = stock.history(start=start_date, end=end_date)
                show_news_impact(valid_news, hist, ticker_symbol)
                
    except Exception as e:
        logger.error(f"Error in show_news_sentiment: {str(e)}\n{traceback.format_exc()}")
        st.error("Error fetching news data. Please try again later.")
        
        # Show a more user-friendly error message
        st.info("While we're experiencing technical difficulties, you can:")
        st.write("1. Refresh the page")
        st.write("2. Check your internet connection")
        st.write("3. Try again in a few minutes")
        st.write("4. Visit the news sources directly using the links below")
        
        # Show direct links to news sections
        st.markdown(f"[Yahoo Finance {ticker_symbol}](https://finance.yahoo.com/quote/{ticker_symbol}/news)")
        st.markdown(f"[MarketWatch {ticker_symbol}](https://www.marketwatch.com/investing/stock/{ticker_symbol}/news)")
        st.markdown(f"[Seeking Alpha {ticker_symbol}](https://seekingalpha.com/symbol/{ticker_symbol}/news)")

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