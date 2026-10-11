"""Tests for components.dividends.

The dictionaries use the key names of yfinance's ``Ticker.info``. Unless a
test says otherwise the figures are invented and small enough to check by
hand: a dividend of 2 a year on a price of 80 is a yield of 2.5%.

``Ticker.info`` comes in two forms, which differ in the unit of
``dividendYield``:

- merged: yfinance 0.2.53 and later lay Yahoo's v7 quote endpoint over its
  quoteSummary endpoint. ``dividendYield`` is a percentage and
  ``regularMarketPrice`` is present.
- quoteSummary alone: yfinance 0.2.37 to 0.2.52, and yfinance from 1.5.1 on
  when the v7 request fails with an HTTP error. ``dividendYield`` is a
  fraction and there is no ``regularMarketPrice``.
"""

import pytest

from components.dividends import dividend_yield_percent


def share(**changes):
    """A share that pays a dividend, in the merged form, with changes applied.

    A change to None removes the key: yfinance leaves out what Yahoo does not
    send.
    """
    info = {
        'quoteType': 'EQUITY',
        'currency': 'USD',
        'dividendRate': 2.0,
        'dividendYield': 2.5,                   # a percentage in this form
        'trailingAnnualDividendYield': 0.024,   # a fraction in both forms
        'currentPrice': 80.0,
        'regularMarketPrice': 80.0,
        'previousClose': 100.0,
        'regularMarketPreviousClose': 100.0,
    }
    info.update(changes)
    return {key: value for key, value in info.items() if value is not None}


# The yield of a share

def test_yield_is_the_dividend_rate_over_the_price():
    # 2 a year on a price of 80
    assert dividend_yield_percent({'dividendRate': 2.0, 'currentPrice': 80.0}) == pytest.approx(2.5)


def test_whole_numbers_are_accepted():
    assert dividend_yield_percent({'dividendRate': 2, 'currentPrice': 80}) == pytest.approx(2.5)


def test_both_forms_of_info_give_the_same_yield():
    merged = share()
    quote_summary_alone = share(dividendYield=0.025, regularMarketPrice=None)

    assert dividend_yield_percent(merged) == pytest.approx(2.5)
    assert dividend_yield_percent(quote_summary_alone) == pytest.approx(2.5)


@pytest.mark.parametrize('reported', [0.025, 2.5, 250.0, None])
def test_the_size_of_dividend_yield_does_not_change_the_result(reported):
    assert dividend_yield_percent(share(dividendYield=reported)) == pytest.approx(2.5)


# The fields the function reads, as Yahoo returned them on 10 October 2026,
# and Yahoo's own dividendYield from the v7 endpoint, a percentage.
YAHOO_ON_10_OCTOBER_2026 = {
    'AAPL': ({'currency': 'USD', 'dividendRate': 1.08, 'currentPrice': 336.64}, 0.32),
    'TM': ({'currency': 'USD', 'dividendRate': 6.27, 'currentPrice': 185.3}, 3.37),
    'HSBA.L': ({'currency': 'GBp', 'dividendRate': 0.56, 'currentPrice': 1395.8}, 3.95),
    'NPN.JO': ({'currency': 'ZAc', 'dividendRate': 5.08, 'currentPrice': 72169.0}, 0.72),
    'LUMI.TA': ({'currency': 'ILA', 'dividendRate': 3.08, 'currentPrice': 7154.0}, 4.27),
    'NBK.KW': ({'currency': 'KWF', 'dividendRate': 0.04, 'currentPrice': 820.0}, 4.23),
}


@pytest.mark.parametrize('as_fraction', [False, True])
@pytest.mark.parametrize('symbol', sorted(YAHOO_ON_10_OCTOBER_2026))
def test_real_figures_give_about_the_yield_yahoo_reports(symbol, as_fraction):
    fields, yahoo_percent = YAHOO_ON_10_OCTOBER_2026[symbol]
    reported = yahoo_percent / 100 if as_fraction else yahoo_percent
    info = dict(fields, dividendYield=reported)

    # A mistake in the unit would be out by a factor of 100 or 1000. The
    # differences that remain are small: Yahoo gives the dividend rate to two
    # decimal places (0.04 for NBK.KW) and does not work its own figure out
    # from this price.
    assert dividend_yield_percent(info) == pytest.approx(yahoo_percent, rel=0.2)


def test_aapl_shows_as_0_32_percent_in_both_forms():
    # 1.08 / 336.64 = 0.3208%. The reported 0.32 times 100 would be 32.00%.
    fields, _ = YAHOO_ON_10_OCTOBER_2026['AAPL']

    for reported in (0.32, 0.0032):
        value = dividend_yield_percent(dict(fields, dividendYield=reported))
        assert f'{value:.2f}%' == '0.32%'


# Which price

PRICE_KEYS_LATEST_FIRST = ['currentPrice', 'regularMarketPrice', 'previousClose', 'regularMarketPreviousClose']


@pytest.mark.parametrize('key', PRICE_KEYS_LATEST_FIRST)
def test_each_price_field_can_supply_the_price(key):
    assert dividend_yield_percent({'dividendRate': 2.0, key: 80.0}) == pytest.approx(2.5)


def test_price_fields_are_tried_latest_first():
    info = {
        'dividendRate': 2.0,
        'currentPrice': 80.0,                   # 2 / 80 = 2.5%
        'regularMarketPrice': 100.0,            # 2 / 100 = 2%
        'previousClose': 125.0,                 # 2 / 125 = 1.6%
        'regularMarketPreviousClose': 160.0,    # 2 / 160 = 1.25%
    }

    for key, expected in zip(PRICE_KEYS_LATEST_FIRST, [2.5, 2.0, 1.6, 1.25]):
        assert dividend_yield_percent(info) == pytest.approx(expected)
        del info[key]
    assert dividend_yield_percent(info) is None


@pytest.mark.parametrize('unusable', [None, 0, 0.0, -80.0, float('nan'), float('inf'), '80.0', True])
def test_an_unusable_price_is_passed_over(unusable):
    info = {'dividendRate': 2.0, 'currentPrice': unusable, 'previousClose': 100.0}

    assert dividend_yield_percent(info) == pytest.approx(2.0)


def test_a_share_with_no_price_has_no_yield():
    info = share(currentPrice=None, regularMarketPrice=None, previousClose=None, regularMarketPreviousClose=None)

    # dividendYield is there, but nothing says which unit it is in
    assert info['dividendRate'] == 2.0 and info['dividendYield'] == 2.5
    assert dividend_yield_percent(info) is None


# Prices in a sub-unit of the currency

@pytest.mark.parametrize('currency, price', [
    ('GBp', 8000.0),     # pence: 80 pounds
    ('ZAc', 8000.0),     # cents: 80 rand
    ('ILA', 8000.0),     # agorot: 80 shekels
    ('KWF', 80000.0),    # fils: 80 dinars
])
def test_a_price_in_a_sub_unit_is_converted_before_dividing(currency, price):
    info = share(currency=currency, currentPrice=price)

    # the dividend rate stays in the main unit: 2 on 80
    assert dividend_yield_percent(info) == pytest.approx(2.5)


@pytest.mark.parametrize('currency', ['USD', 'GBP', 'gbp', 'ZAR', 'ILS', 'KWD', 'JPY', '', None, 100, ['GBp']])
def test_a_price_in_any_other_currency_is_used_as_it_is(currency):
    assert dividend_yield_percent(share(currency=currency)) == pytest.approx(2.5)


# Funds

def test_a_fund_gives_its_own_yield_in_both_forms():
    # SCHD on 10 October 2026. It has no dividendRate, and without the v7
    # endpoint it has no dividendYield either.
    merged = {
        'quoteType': 'ETF',
        'yield': 0.0324,
        'dividendYield': 3.24,
        'trailingAnnualDividendYield': 0.0,
        'regularMarketPrice': 33.04,
        'previousClose': 33.15,
    }
    quote_summary_alone = {
        'quoteType': 'ETF',
        'yield': 0.0324,
        'trailingAnnualDividendYield': 0.0,
        'previousClose': 33.15,
    }

    assert dividend_yield_percent(merged) == pytest.approx(3.24)
    assert dividend_yield_percent(quote_summary_alone) == pytest.approx(3.24)


def test_a_fund_yield_is_used_before_a_dividend_rate():
    # VFIAX on 10 October 2026: 5.6485 / 721.04 is 0.78%, but both of Yahoo's
    # yield fields put the fund at 1.05%
    info = {
        'quoteType': 'MUTUALFUND',
        'yield': 0.0105,
        'dividendYield': 1.05,
        'dividendRate': 5.6485,
        'regularMarketPrice': 721.04,
    }

    assert dividend_yield_percent(info) == pytest.approx(1.05)


@pytest.mark.parametrize('info', [
    {'quoteType': 'ETF', 'yield': 0.0, 'dividendYield': 0.0, 'regularMarketPrice': 384.58, 'previousClose': 378.62},
    {'quoteType': 'ETF', 'yield': 0.0, 'previousClose': 378.62},    # quoteSummary alone
])
def test_a_fund_that_pays_nothing_has_a_yield_of_zero(info):
    # GLD on 10 October 2026
    result = dividend_yield_percent(info)

    assert result is not None
    assert result == 0.0


@pytest.mark.parametrize('fund_yield', [None, '0.0324', float('nan'), -0.01, True])
def test_an_unusable_fund_yield_leaves_the_dividend_rate_and_price(fund_yield):
    info = share()
    info['yield'] = fund_yield

    assert dividend_yield_percent(info) == pytest.approx(2.5)


# No dividend

@pytest.mark.parametrize('reported', [0, 0.0])
def test_a_company_that_pays_no_dividend_has_a_yield_of_zero(reported):
    # Yahoo sends no dividendRate for such a company, in either form
    info = {
        'quoteType': 'EQUITY',
        'dividendYield': reported,
        'trailingAnnualDividendYield': 0.0,
        'currentPrice': 250.0,
        'previousClose': 245.0,
    }

    result = dividend_yield_percent(info)

    assert result is not None
    assert result == 0.0


@pytest.mark.parametrize('info', [
    {'dividendRate': 0.0, 'dividendYield': 0.0, 'currentPrice': 4.5},
    {'dividendRate': 0.0, 'dividendYield': 2.5, 'currentPrice': 4.5},
    {'dividendRate': 0.0},
    {'dividendRate': 0},
])
def test_a_dividend_rate_of_zero_is_a_yield_of_zero_whatever_else_is_there(info):
    result = dividend_yield_percent(info)

    assert result is not None
    assert result == 0.0


def test_a_dividend_yield_of_zero_does_not_cancel_a_dividend_rate():
    assert dividend_yield_percent(share(dividendYield=0.0)) == pytest.approx(2.5)


# Nothing to work the yield out from

@pytest.mark.parametrize('info', [
    None,
    'AAPL',
    3,
    [],
    {},
    # yfinance 1.7.0's answer for a symbol Yahoo does not know
    {'trailingPegRatio': None},
    {'quoteType': 'INDEX', 'previousClose': 5000.0},
    # a company that pays nothing, from yfinance 0.2.37 to 0.2.52, which
    # leave out every field that is zero
    {'quoteType': 'EQUITY', 'currentPrice': 250.0, 'previousClose': 245.0},
])
def test_no_dividend_fields_give_none(info):
    assert dividend_yield_percent(info) is None


@pytest.mark.parametrize('reported', [0.025, 2.5])
def test_dividend_yield_on_its_own_is_not_used(reported):
    assert dividend_yield_percent({'dividendYield': reported, 'currentPrice': 80.0}) is None


def test_the_trailing_yield_is_not_used():
    # SONY on 10 October 2026, without its dividendRate: Yahoo divided 25 yen
    # on an ordinary share by the 23.95 dollar previous close of the receipt
    info = {
        'trailingAnnualDividendRate': 25.0,
        'trailingAnnualDividendYield': 1.0438414,
        'currentPrice': 24.12,
        'previousClose': 23.95,
    }

    assert dividend_yield_percent(info) is None


@pytest.mark.parametrize('rate', ['2.0', float('nan'), float('inf'), -2.0, True, [2.0]])
def test_an_unusable_dividend_rate_counts_as_missing(rate):
    assert dividend_yield_percent(share(dividendRate=rate)) is None


def test_the_dictionary_is_left_unchanged():
    info = share(currency='GBp')
    before = dict(info)

    dividend_yield_percent(info)

    assert info == before
