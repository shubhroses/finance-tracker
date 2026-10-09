"""Tests for the order in which get_stock_news tries its sources.

yfinance, the HTTP session and time.sleep are replaced by fakes, so these
tests make no network calls and do not wait.
"""

from types import SimpleNamespace

import pytest

from components import utils

FLAT_ITEM = {
    'title': 'Example Corp raises its full-year outlook',
    'link': 'https://finance.example.com/news/example-corp-raises-outlook-100000001.html',
    'publisher': 'Example Wire',
    'providerPublishTime': 1735693200,
    'type': 'STORY',
}
NESTED_ITEM = {
    'id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    'content': {
        'title': 'Example Corp raises its full-year outlook',
        'pubDate': '2025-01-01T01:00:00Z',
        'canonicalUrl': {'url': 'https://finance.example.com/news/example-corp-raises-outlook-100000001.html'},
    },
}


@pytest.fixture
def sources(monkeypatch):
    """Fake every source get_stock_news can reach and record what it calls.

    Set ``ticker_news`` and ``search_news`` to the list a source should
    return, or to an exception it should raise. The scraped Yahoo page always
    answers 404.
    """
    state = SimpleNamespace(ticker_news=[], search_news=[], calls=[])

    def result_of(value):
        if isinstance(value, Exception):
            raise value
        return value

    class FakeTicker:
        def __init__(self, symbol):
            state.calls.append(('Ticker', symbol))

        @property
        def news(self):
            return result_of(state.ticker_news)

    class FakeSearch:
        def __init__(self, query, news_count=8):
            state.calls.append(('Search', query, news_count))
            self.news = result_of(state.search_news)

    class FakeSession:
        def get(self, url, timeout=None):
            state.calls.append(('GET', url))
            return SimpleNamespace(status_code=404, text='')

    monkeypatch.setattr(utils, 'yf', SimpleNamespace(Ticker=FakeTicker, Search=FakeSearch))
    monkeypatch.setattr(utils, 'get_session', FakeSession)
    monkeypatch.setattr(utils, 'time', SimpleNamespace(sleep=lambda seconds: None))

    # get_stock_news is wrapped in st.cache_data: start and end with no entries
    utils.get_stock_news.clear()
    yield state
    utils.get_stock_news.clear()


def kinds(calls):
    return [call[0] for call in calls]


def test_ticker_news_is_returned_without_asking_the_search(sources):
    sources.ticker_news = [NESTED_ITEM]
    sources.search_news = [FLAT_ITEM]

    assert utils.get_stock_news('TEST') == [NESTED_ITEM]
    assert kinds(sources.calls) == ['Ticker']


def test_search_is_asked_when_ticker_news_is_empty(sources):
    sources.ticker_news = []
    sources.search_news = [FLAT_ITEM]

    assert utils.get_stock_news('TEST') == [FLAT_ITEM]
    assert sources.calls == [('Ticker', 'TEST'), ('Search', 'TEST', 10)]


def test_search_is_asked_when_ticker_news_raises(sources):
    sources.ticker_news = RuntimeError('Yahoo answered 404')
    sources.search_news = [FLAT_ITEM]

    assert utils.get_stock_news('TEST') == [FLAT_ITEM]
    assert kinds(sources.calls) == ['Ticker', 'Search']


def test_page_scrape_follows_a_failed_search_and_every_attempt_repeats_the_order(sources):
    sources.ticker_news = []
    sources.search_news = RuntimeError('search is down')

    assert utils.get_stock_news('TEST', max_retries=2) is None
    assert kinds(sources.calls) == ['Ticker', 'Search', 'GET', 'Ticker', 'Search', 'GET']
    assert sources.calls[2] == ('GET', 'https://finance.yahoo.com/quote/TEST/news')


def test_lookup_goes_on_to_the_page_scrape_when_yfinance_has_no_search(sources, monkeypatch):
    # yfinance releases before 0.2.51 have no Search class
    monkeypatch.delattr(utils.yf, 'Search')
    sources.ticker_news = []

    assert utils.get_stock_news('TEST', max_retries=1) is None
    assert kinds(sources.calls) == ['Ticker', 'GET']
