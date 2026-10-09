"""Tests for components.indicators on price series small enough to check by hand.

The expected values in each test are worked out in the comments above them.
"""

import numpy as np
import pandas as pd
import pytest

from components.indicators import (
    calculate_atr,
    calculate_bollinger_bands,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)

NAN = float('nan')


def assert_values(series, expected):
    """Compare a Series with a list of floats; NaN must match NaN."""
    assert len(series) == len(expected)
    np.testing.assert_allclose(series.to_numpy(dtype=float), expected, rtol=1e-12, atol=1e-12)


# Simple moving average

def test_sma_is_the_mean_of_the_last_window_values():
    prices = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 9.0])

    # (1+2+3)/3 = 2, (2+3+4)/3 = 3, (3+4+5)/3 = 4, (4+5+9)/3 = 6
    assert_values(calculate_sma(prices, window=3), [NAN, NAN, 2.0, 3.0, 4.0, 6.0])


def test_sma_with_a_window_of_one_is_the_series_itself():
    prices = pd.Series([3.0, 1.0, 4.0])

    assert_values(calculate_sma(prices, window=1), [3.0, 1.0, 4.0])


def test_sma_is_all_nan_when_the_series_is_shorter_than_the_window():
    prices = pd.Series([1.0, 2.0])

    assert calculate_sma(prices, window=3).isna().all()


def test_sma_keeps_the_index_of_the_prices():
    index = pd.date_range('2025-01-01', periods=4, freq='D')
    prices = pd.Series([1.0, 2.0, 3.0, 4.0], index=index)

    assert calculate_sma(prices, window=2).index.equals(index)


# RSI

def test_rsi_over_three_changes():
    prices = pd.Series([10.0, 12.0, 11.0, 12.0, 13.0, 14.0, 13.0, 12.0, 11.0])
    # changes:                +2    -1    +1    +1    +1    -1    -1    -1
    #
    # index 3: changes +2 -1 +1 -> mean gain 1,   mean loss 1/3, RS 3,   RSI 75
    # index 4: changes -1 +1 +1 -> mean gain 2/3, mean loss 1/3, RS 2,   RSI 66.67
    # index 5: changes +1 +1 +1 -> no losses                             RSI 100
    # index 6: changes +1 +1 -1 -> mean gain 2/3, mean loss 1/3, RS 2,   RSI 66.67
    # index 7: changes +1 -1 -1 -> mean gain 1/3, mean loss 2/3, RS 1/2, RSI 33.33
    # index 8: changes -1 -1 -1 -> no gains                              RSI 0
    expected = [NAN, NAN, NAN, 75.0, 200 / 3, 100.0, 200 / 3, 100 / 3, 0.0]

    assert_values(calculate_rsi(prices, periods=3), expected)


def test_rsi_default_period_is_fourteen_changes():
    # Seven rises of 1 then seven falls of 1: the fourteen changes balance,
    # so RS is 1 and RSI is 50. Fourteen changes need fifteen prices.
    prices = pd.Series([10.0 + step for step in range(8)] + [17.0 - step for step in range(1, 8)])

    rsi = calculate_rsi(prices)

    assert len(prices) == 15
    assert rsi.iloc[:14].isna().all()
    assert rsi.iloc[14] == pytest.approx(50.0)


def test_rsi_is_nan_while_prices_do_not_move():
    prices = pd.Series([5.0, 5.0, 5.0, 5.0, 5.0])

    # No gains and no losses: RS is 0/0
    assert calculate_rsi(prices, periods=3).isna().all()


def test_rsi_stays_between_0_and_100():
    prices = pd.Series([10.0, 10.5, 9.8, 10.9, 11.4, 10.2, 10.3, 12.0, 11.1, 11.6, 10.7, 10.8])

    rsi = calculate_rsi(prices, periods=4).dropna()

    assert len(rsi) == 8
    assert ((rsi >= 0) & (rsi <= 100)).all()


# MACD

def test_macd_with_short_periods():
    prices = pd.Series([8.0, 16.0, 16.0, 8.0])
    # A period of 3 gives alpha 1/2 and a period of 7 gives alpha 1/4.
    #
    # fast EMA (alpha 1/2): 8, 8 + (16-8)/2 = 12, 12 + (16-12)/2 = 14,   14 + (8-14)/2 = 11
    # slow EMA (alpha 1/4): 8, 8 + (16-8)/4 = 10, 10 + (16-10)/4 = 11.5, 11.5 + (8-11.5)/4 = 10.625
    # MACD = fast - slow:   0, 2, 2.5, 0.375
    # signal (alpha 1/2):   0, 0 + (2-0)/2 = 1, 1 + (2.5-1)/2 = 1.75, 1.75 + (0.375-1.75)/2 = 1.0625
    # histogram:            0, 1, 0.75, -0.6875
    macd = calculate_macd(prices, fast=3, slow=7, signal=3)

    assert list(macd.columns) == ['MACD', 'Signal', 'Histogram']
    assert_values(macd['MACD'], [0.0, 2.0, 2.5, 0.375])
    assert_values(macd['Signal'], [0.0, 1.0, 1.75, 1.0625])
    assert_values(macd['Histogram'], [0.0, 1.0, 0.75, -0.6875])


def ema(values, period):
    """Reference EMA written as the textbook recursion."""
    alpha = 2 / (period + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append(result[-1] + alpha * (value - result[-1]))
    return result


def test_macd_default_periods_are_12_26_and_9():
    values = [100.0, 101.5, 99.0, 102.0, 104.5, 103.0, 105.0, 107.5, 106.0, 108.0,
              110.5, 109.0, 111.0, 113.5, 112.0, 114.0, 116.5, 115.0, 117.0, 119.5,
              118.0, 120.0, 122.5, 121.0, 123.0, 125.5, 124.0, 126.0, 128.5, 127.0]
    expected_macd = [fast - slow for fast, slow in zip(ema(values, 12), ema(values, 26))]
    expected_signal = ema(expected_macd, 9)

    macd = calculate_macd(pd.Series(values))

    assert_values(macd['MACD'], expected_macd)
    assert_values(macd['Signal'], expected_signal)
    assert_values(macd['Histogram'], [m - s for m, s in zip(expected_macd, expected_signal)])


def test_macd_is_zero_for_constant_prices():
    macd = calculate_macd(pd.Series([42.0] * 40))

    # Both averages stay at 42, so their difference and its average are 0
    np.testing.assert_allclose(macd.to_numpy(), 0.0, rtol=0, atol=1e-12)


# Bollinger Bands

def test_bollinger_middle_band_is_the_moving_average():
    prices = pd.Series([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0, 11.0])

    bands = calculate_bollinger_bands(prices, window=8, num_std=2)

    # (2+4+4+4+5+5+7+9)/8 = 5 and (4+4+4+5+5+7+9+11)/8 = 6.125
    assert list(bands.columns) == ['Middle', 'Upper', 'Lower']
    assert_values(bands['Middle'], [NAN] * 7 + [5.0, 6.125])
    assert bands.iloc[:7].isna().all().all()


def test_bollinger_bands_are_the_same_distance_either_side_of_the_middle():
    prices = pd.Series([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0, 11.0])

    bands = calculate_bollinger_bands(prices, window=8, num_std=2).dropna()

    assert len(bands) == 2
    np.testing.assert_allclose(bands['Upper'] - bands['Middle'], bands['Middle'] - bands['Lower'])
    assert (bands['Upper'] > bands['Middle']).all()


def test_bollinger_band_distance_scales_with_the_number_of_deviations():
    prices = pd.Series([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])

    one = calculate_bollinger_bands(prices, window=8, num_std=1).iloc[-1]
    three = calculate_bollinger_bands(prices, window=8, num_std=3).iloc[-1]

    assert three['Upper'] - three['Middle'] == pytest.approx(3 * (one['Upper'] - one['Middle']))


def test_bollinger_bands_collapse_onto_constant_prices():
    bands = calculate_bollinger_bands(pd.Series([7.0] * 5), window=3, num_std=2).dropna()

    # No spread in any window, so the deviation is 0 and all three bands are 7
    assert len(bands) == 3
    np.testing.assert_allclose(bands.to_numpy(), 7.0, rtol=0, atol=1e-12)


def test_bollinger_defaults_are_twenty_periods():
    prices = pd.Series(np.arange(1.0, 26.0))

    bands = calculate_bollinger_bands(prices)

    # First full window is 1..20, whose mean is 10.5
    assert bands['Middle'].iloc[:19].isna().all()
    assert bands['Middle'].iloc[19] == pytest.approx(10.5)


# ATR

@pytest.fixture
def bars():
    """Five bars that exercise each case of the true range.

    row  high  low  close  high-low  |high-prev close|  |low-prev close|  true range
      0    10    8      9         2                  -                 -           2
      1    11    9     10         2                  2                 0           2
      2    14   12     13         2                  4                 2           4  (gap up)
      3    12    9     10         3                  1                 4           4  (gap down)
      4    12    6      8         6                  2                 4           6
    """
    return pd.DataFrame({
        'High': [10.0, 11.0, 14.0, 12.0, 12.0],
        'Low': [8.0, 9.0, 12.0, 9.0, 6.0],
        'Close': [9.0, 10.0, 13.0, 10.0, 8.0],
    })


def test_atr_with_a_window_of_one_is_the_true_range(bars):
    assert_values(calculate_atr(bars, window=1), [2.0, 2.0, 4.0, 4.0, 6.0])


def test_atr_is_the_mean_true_range_over_the_window(bars):
    # true range 2 2 4 4 6 -> pairs average 2, 3, 4, 5; triples 8/3, 10/3, 14/3
    assert_values(calculate_atr(bars, window=2), [NAN, 2.0, 3.0, 4.0, 5.0])
    assert_values(calculate_atr(bars, window=3), [NAN, NAN, 8 / 3, 10 / 3, 14 / 3])


def test_atr_default_window_is_fourteen():
    # Every bar spans 2 and closes in the middle, so every true range is 2
    rows = 16
    flat = pd.DataFrame({'High': [11.0] * rows, 'Low': [9.0] * rows, 'Close': [10.0] * rows})

    atr = calculate_atr(flat)

    assert atr.iloc[:13].isna().all()
    assert_values(atr.iloc[13:], [2.0, 2.0, 2.0])


# The functions return new objects

def test_inputs_are_left_unchanged(bars):
    prices = pd.Series([10.0, 12.0, 11.0, 12.0, 13.0])
    prices_before = prices.copy()
    bars_before = bars.copy()

    calculate_sma(prices, window=2)
    calculate_rsi(prices, periods=2)
    calculate_macd(prices)
    calculate_bollinger_bands(prices, window=2)
    calculate_atr(bars, window=2)

    pd.testing.assert_series_equal(prices, prices_before)
    pd.testing.assert_frame_equal(bars, bars_before)
