"""Indicator calculations for the Technical Analysis tab.

Plain pandas functions with no Streamlit, plotting or network access, so they
can be imported and tested on their own. Each returns a new Series or
DataFrame on the index of its input and leaves the input unchanged.
"""

import pandas as pd


def calculate_sma(prices, window):
    """Simple moving average: the mean of the last ``window`` values.

    The first ``window - 1`` results are NaN.
    """
    return prices.rolling(window=window).mean()


def calculate_rsi(prices, periods=14):
    """Relative Strength Index from simple averages of gains and losses.

    RSI = 100 - 100 / (1 + RS), where RS is the mean gain over the last
    ``periods`` price changes divided by the mean loss over the same changes.
    The means are simple rolling means, not Wilder's smoothing, so the values
    differ from charting tools that follow Wilder.

    The first ``periods`` results are NaN. A window with no losses gives 100,
    one with no gains gives 0, and one with no price change at all gives NaN.
    """
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=periods).mean()
    avg_loss = loss.rolling(window=periods).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """MACD line, signal line and histogram.

    MACD is the ``fast``-period exponential moving average (EMA) of the
    prices minus the ``slow``-period EMA. The signal line is the
    ``signal``-period EMA of MACD, and the histogram is MACD minus the signal
    line. Each EMA starts at the first value and then moves by
    alpha = 2 / (period + 1) of the distance to each new value.

    Returns a DataFrame with the columns MACD, Signal and Histogram.
    """
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({
        'MACD': macd,
        'Signal': signal_line,
        'Histogram': macd - signal_line,
    })


def calculate_bollinger_bands(prices, window=20, num_std=2):
    """Bollinger Bands: a moving average and a band either side of it.

    The middle band is the ``window``-period simple moving average. The upper
    and lower bands are ``num_std`` standard deviations of the same
    ``window`` values above and below it. Bollinger Bands are defined with
    the population standard deviation (divisor ``window``, not
    ``window - 1``), so ``ddof=0`` replaces the pandas default.

    Returns a DataFrame with the columns Middle, Upper and Lower. The first
    ``window - 1`` rows are NaN.
    """
    rolling = prices.rolling(window=window)
    middle = rolling.mean()
    offset = rolling.std(ddof=0) * num_std
    return pd.DataFrame({
        'Middle': middle,
        'Upper': middle + offset,
        'Lower': middle - offset,
    })


def calculate_atr(df, window=14):
    """Average True Range: a simple mean of the true range over ``window`` rows.

    The true range of a row is the largest of high - low,
    |high - previous close| and |low - previous close|. The first row has no
    previous close, so its true range is high - low. The mean is a simple
    rolling mean, not Wilder's smoothing.

    ``df`` needs High, Low and Close columns. The first ``window - 1`` results
    are NaN.
    """
    high = df['High']
    low = df['Low']
    previous_close = df['Close'].shift(1)

    true_range = pd.DataFrame({
        'range': high - low,
        'high_gap': (high - previous_close).abs(),
        'low_gap': (low - previous_close).abs(),
    }).max(axis=1)
    return true_range.rolling(window=window).mean()
