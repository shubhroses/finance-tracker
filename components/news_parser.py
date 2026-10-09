"""Turn raw yfinance news items into the fields the News tab displays.

yfinance hands back Yahoo's news JSON unchanged, and the two Yahoo endpoints
it has used lay an item out differently. The functions here accept both
layouts. They use no Streamlit, network or clock access, so they can be
imported and tested on their own.
"""

from datetime import datetime, timezone

DEFAULT_PUBLISHER = 'Yahoo Finance'
DEFAULT_TYPE = 'STORY'


def parse_news_item(item):
    """Return the display fields for one news item, or None if it is unusable.

    Two layouts are accepted:

    * Flat, as ``Ticker.news`` returned up to yfinance 0.2.50 and as
      ``yfinance.Search(...).news`` still returns::

          {'title': ..., 'link': ..., 'publisher': ...,
           'providerPublishTime': 1735689600, 'type': 'STORY'}

    * Nested under ``content``, as ``Ticker.news`` returns from yfinance
      0.2.51 on::

          {'id': ..., 'content': {
              'title': ..., 'summary': ..., 'contentType': 'STORY',
              'pubDate': '2025-01-01T00:00:00Z',
              'provider': {'displayName': ...},
              'canonicalUrl': {'url': ...},
              'clickThroughUrl': {'url': ...}}}

    The result has the keys ``title``, ``link``, ``publisher``, ``published``,
    ``summary`` and ``type``. ``published`` is a timezone-aware UTC datetime,
    or None when the item carries no readable time. An item with no title or
    no link cannot be shown as a headline, so it gives None.
    """
    if not isinstance(item, dict):
        return None

    content = item.get('content')
    if isinstance(content, dict):
        article = _parse_nested(content)
    else:
        article = _parse_flat(item)

    if not article['title'] or not article['link']:
        return None
    return article


def parse_news_items(items):
    """Parse a list of raw items, drop the unusable ones and sort newest first.

    Items without a publish time keep their relative order and go last.
    """
    articles = [parse_news_item(item) for item in items or []]
    articles = [article for article in articles if article is not None]
    articles.sort(key=_newest_first_key, reverse=True)
    return articles


def _parse_flat(item):
    return {
        'title': _text(item.get('title')),
        'link': _text(item.get('link')),
        'publisher': _text(item.get('publisher')) or DEFAULT_PUBLISHER,
        'published': _from_epoch(item.get('providerPublishTime')),
        'summary': _text(item.get('summary')),
        'type': _text(item.get('type')) or DEFAULT_TYPE,
    }


def _parse_nested(content):
    provider = content.get('provider')
    publisher = _text(provider.get('displayName')) if isinstance(provider, dict) else ''
    # clickThroughUrl is Yahoo's own copy of the article. It is null when Yahoo
    # does not host the article; canonicalUrl is then the publisher's page and
    # previewUrl an address on Yahoo's site.
    link = (
        _url(content.get('clickThroughUrl'))
        or _url(content.get('canonicalUrl'))
        or _text(content.get('previewUrl'))
    )
    return {
        'title': _text(content.get('title')),
        'link': link,
        'publisher': publisher or DEFAULT_PUBLISHER,
        'published': _from_iso(content.get('pubDate')) or _from_iso(content.get('displayTime')),
        'summary': _text(content.get('summary')) or _text(content.get('description')),
        'type': _text(content.get('contentType')) or DEFAULT_TYPE,
    }


def _text(value):
    """Return a string value stripped of surrounding whitespace, else ''."""
    return value.strip() if isinstance(value, str) else ''


def _url(link):
    """Return the address inside a Yahoo link object such as canonicalUrl."""
    return _text(link.get('url')) if isinstance(link, dict) else ''


def _from_epoch(value):
    """Convert Unix seconds (or milliseconds) to an aware UTC datetime."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value <= 0:
        return None
    if value > 1e11:  # 1e11 seconds is the year 5138, so this is milliseconds
        value = value / 1000
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _from_iso(value):
    """Convert an ISO 8601 string such as '2025-01-01T00:00:00Z' to UTC."""
    text = _text(value)
    if not text:
        return None
    if text[-1] in 'Zz':
        # datetime.fromisoformat only accepts the Z suffix from Python 3.11
        text = text[:-1] + '+00:00'
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _newest_first_key(article):
    """Sort key that puts dated articles ahead of undated ones in a reverse sort."""
    published = article['published']
    if published is None:
        return (False, datetime.min.replace(tzinfo=timezone.utc))
    return (True, published)
