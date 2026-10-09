"""Tests for components.news_parser.

The fixtures hold the two layouts yfinance has used for a news item. Their
keys follow real responses; the headlines, names and addresses are invented.

- fixtures/news_flat.json: the flat layout, as Ticker.news returned up to
  yfinance 0.2.50 and as yfinance.Search(...).news still returns.
- fixtures/news_nested.json: the layout nested under "content", as
  Ticker.news returns from yfinance 0.2.51 on.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from components.news_parser import parse_news_item, parse_news_items

FIXTURES = Path(__file__).parent / 'fixtures'


def load_fixture(name):
    with open(FIXTURES / name, encoding='utf-8') as handle:
        return json.load(handle)


@pytest.fixture
def flat_items():
    return load_fixture('news_flat.json')


@pytest.fixture
def nested_items():
    return load_fixture('news_nested.json')


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_flat_item(flat_items):
    assert parse_news_item(flat_items[0]) == {
        'title': 'Example Corp raises its full-year outlook',
        'link': 'https://finance.example.com/news/example-corp-raises-outlook-100000001.html',
        'publisher': 'Example Wire',
        'published': utc(2025, 1, 1, 1, 0, 0),
        'summary': '',
        'type': 'STORY',
    }


def test_nested_item(nested_items):
    assert parse_news_item(nested_items[0]) == {
        'title': 'Example Corp raises its full-year outlook',
        'link': 'https://finance.example.com/news/example-corp-raises-outlook-100000001.html',
        'publisher': 'Example Wire',
        'published': utc(2025, 1, 1, 1, 0, 0),
        'summary': 'The company now expects revenue to grow 12% this year.',
        'type': 'STORY',
    }


def test_same_article_gives_the_same_headline_fields_in_both_layouts(flat_items, nested_items):
    flat = parse_news_item(flat_items[0])
    nested = parse_news_item(nested_items[0])

    for field in ('title', 'link', 'publisher', 'published', 'type'):
        assert flat[field] == nested[field]


def test_nested_item_without_click_through_url_links_to_the_publisher(nested_items):
    item = nested_items[1]
    assert item['content']['clickThroughUrl'] is None

    article = parse_news_item(item)

    assert article['link'] == 'https://www.samplejournal.example/articles/chip-makers-lead-a-broad-market-rally'
    assert article['publisher'] == 'Sample Journal'
    assert article['published'] == utc(2025, 1, 1, 0, 0, 0)


def test_nested_item_with_only_a_preview_url_links_to_it(nested_items):
    item = nested_items[1]
    item['content']['canonicalUrl'] = None

    assert parse_news_item(item)['link'] == (
        'https://finance.example.com/m/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb/chip-makers-lead.html'
    )


def test_nested_item_falls_back_to_display_time_and_description(nested_items):
    content = nested_items[0]['content']
    content['pubDate'] = None
    content['summary'] = ''
    content['description'] = 'Longer text from the description field.'

    article = parse_news_item(nested_items[0])

    assert article['published'] == utc(2025, 1, 1, 1, 5, 0)
    assert article['summary'] == 'Longer text from the description field.'


@pytest.mark.parametrize('fixture_name', ['news_flat.json', 'news_nested.json'])
def test_every_fixture_item_is_usable(fixture_name):
    items = load_fixture(fixture_name)

    articles = parse_news_items(items)

    assert len(articles) == len(items)
    for article in articles:
        assert set(article) == {'title', 'link', 'publisher', 'published', 'summary', 'type'}
        assert article['title'] and article['link'] and article['publisher']
        assert article['published'].tzinfo is timezone.utc


@pytest.mark.parametrize('item', [
    None,
    'a string, not an item',
    {},
    {'title': 'A headline with no link', 'publisher': 'Example Wire'},
    {'link': 'https://finance.example.com/news/no-title.html'},
    {'title': '   ', 'link': 'https://finance.example.com/news/blank-title.html'},
    {'id': 'x', 'content': {}},
    {'id': 'x', 'content': {'title': 'Nested headline with no address', 'clickThroughUrl': None}},
    {'id': 'x', 'content': {'canonicalUrl': {'url': 'https://finance.example.com/news/no-title.html'}}},
])
def test_item_without_a_title_or_a_link_is_rejected(item):
    assert parse_news_item(item) is None


def test_missing_optional_fields_get_defaults():
    flat = parse_news_item({'title': 'Headline', 'link': 'https://finance.example.com/a'})
    nested = parse_news_item({'content': {
        'title': 'Headline',
        'canonicalUrl': {'url': 'https://finance.example.com/a'},
    }})

    expected = {
        'title': 'Headline',
        'link': 'https://finance.example.com/a',
        'publisher': 'Yahoo Finance',
        'published': None,
        'summary': '',
        'type': 'STORY',
    }
    assert flat == expected
    assert nested == expected


@pytest.mark.parametrize('raw, expected', [
    (1735689600, utc(2025, 1, 1)),              # seconds
    (1735689600.0, utc(2025, 1, 1)),
    (1735689600000, utc(2025, 1, 1)),           # milliseconds
    (0, None),
    (-5, None),
    (float('nan'), None),
    (None, None),
    (True, None),
    ('1735689600', None),
])
def test_flat_publish_time(raw, expected):
    article = parse_news_item({
        'title': 'Headline',
        'link': 'https://finance.example.com/a',
        'providerPublishTime': raw,
    })

    assert article['published'] == expected


@pytest.mark.parametrize('raw, expected', [
    ('2025-01-01T00:00:00Z', utc(2025, 1, 1)),
    ('2025-01-01T00:00:00+00:00', utc(2025, 1, 1)),
    ('2024-12-31T19:00:00-05:00', utc(2025, 1, 1)),   # converted to UTC
    ('2025-01-01T00:00:00', utc(2025, 1, 1)),         # no offset: taken as UTC
    ('not a date', None),
    ('', None),
    (None, None),
    (1735689600, None),
])
def test_nested_publish_time(raw, expected):
    article = parse_news_item({'content': {
        'title': 'Headline',
        'canonicalUrl': {'url': 'https://finance.example.com/a'},
        'pubDate': raw,
    }})

    assert article['published'] == expected


def test_items_are_sorted_newest_first_with_undated_items_last():
    def flat(title, when):
        return {'title': title, 'link': 'https://finance.example.com/' + title, 'providerPublishTime': when}

    def nested(title, when):
        return {'content': {
            'title': title,
            'canonicalUrl': {'url': 'https://finance.example.com/' + title},
            'pubDate': when,
        }}

    items = [
        flat('undated-1', None),
        flat('oldest', 1735689600),                 # 2025-01-01 00:00 UTC
        nested('newest', '2025-01-01T02:00:00Z'),
        {'title': 'no link, dropped'},
        nested('undated-2', None),
        flat('middle', 1735693200),                 # 2025-01-01 01:00 UTC
    ]

    titles = [article['title'] for article in parse_news_items(items)]

    assert titles == ['newest', 'middle', 'oldest', 'undated-1', 'undated-2']


@pytest.mark.parametrize('items', [None, []])
def test_no_items_gives_an_empty_list(items):
    assert parse_news_items(items) == []
