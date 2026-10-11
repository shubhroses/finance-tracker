"""Dividend yield from a yfinance ``Ticker.info`` dictionary.

``info['dividendYield']`` cannot be shown as it stands, because yfinance
passes on Yahoo's figure in one of two units:

* a fraction (0.0032 for a yield of 0.32%), from Yahoo's quoteSummary
  endpoint. yfinance 0.2.37 to 0.2.52 build ``info`` from this endpoint alone.
* a percentage (0.32), from Yahoo's v7 quote endpoint. yfinance 0.2.53 to
  1.7.0, the newest release when this was written, lay that endpoint's fields
  over the first. From 1.5.1 on, when the v7 request fails with an HTTP
  error, ``info`` holds the fraction again.

The dictionary does not record which endpoint a value came from, and a small
figure such as 0.02 is a believable yield in either unit. The function here
therefore works the yield out from fields that have one unit on both
endpoints. It uses no Streamlit or network access, so it can be imported and
tested on its own.
"""

import math

# Currencies in which Yahoo quotes the price in a sub-unit while it gives the
# dividend rate in the main unit, with the number of sub-units in one unit:
# pence in London, cents in Johannesburg, agorot in Tel Aviv, fils in Kuwait.
SUB_UNITS = {'GBp': 100, 'ZAc': 100, 'ILA': 100, 'KWF': 1000}

# Where to look for the price, latest first. currentPrice comes from the
# quoteSummary endpoint and regularMarketPrice from the v7 one. The previous
# close stands in when neither is there.
PRICE_KEYS = ('currentPrice', 'regularMarketPrice', 'previousClose', 'regularMarketPreviousClose')


def dividend_yield_percent(info):
    """Return the dividend yield as a percentage, or None when it is unknown.

    0.32 means 0.32%. The sources, in order:

    * ``yield``, for a fund. Only the quoteSummary endpoint has this field,
      and it is a fraction there.
    * ``dividendRate``, the dividend per share over a year, divided by the
      first price in ``PRICE_KEYS`` that is present. A price in one of the
      ``SUB_UNITS`` is converted to the main unit first. A rate of zero is a
      yield of zero whatever the price.
    * a ``dividendYield`` of zero when there is no ``dividendRate``, which is
      how Yahoo reports a company that pays no dividend. Zero is the same in
      both units, so this is the one value of that field that is used.

    ``trailingAnnualDividendYield`` is a fraction on both endpoints, but it is
    not used. For a depositary receipt Yahoo divides the dividend on one
    ordinary share, in the company's reporting currency, by the price of the
    receipt in dollars: on 10 October 2026 that gave 1.04, or 104%, for SONY.
    """
    if not isinstance(info, dict):
        return None

    fund_yield = _number(info.get('yield'))
    if fund_yield is not None:
        return fund_yield * 100

    rate = _number(info.get('dividendRate'))
    if rate == 0 or (rate is None and _number(info.get('dividendYield')) == 0):
        return 0.0

    prices = (_number(info.get(key)) for key in PRICE_KEYS)
    price = next((price for price in prices if price), None)
    if rate is None or price is None:
        return None

    currency = info.get('currency')
    sub_units = SUB_UNITS.get(currency, 1) if isinstance(currency, str) else 1
    return rate / (price / sub_units) * 100


def _number(value):
    """Return the value if it is a figure that can be used, else None.

    That is a finite number that is not negative. A missing value, text, a
    boolean, NaN, infinity and a negative number all give None.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value < 0:
        return None
    return value
