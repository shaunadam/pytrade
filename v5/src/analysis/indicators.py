import pandas as pd
import numpy as np


def sma(data, period=14):
    """
    Calculate Simple Moving Average
    """
    return data.rolling(window=period).mean()


def ema(data, period=14):
    """
    Calculate Exponential Moving Average
    """
    return data.ewm(span=period, adjust=False).mean()


def rsi(data, period=14):
    """
    Calculate Relative Strength Index
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(data, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculate Moving Average Convergence Divergence (MACD)
    """
    fast_ema = ema(data, fast_period)
    slow_ema = ema(data, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_period)
    macd_histogram = macd_line - signal_line

    return pd.DataFrame(
        {"MACD": macd_line, "Signal": signal_line, "Histogram": macd_histogram}
    )


def bollinger_bands(data, period=20, num_std=2):
    """
    Calculate Bollinger Bands
    """
    sma_line = sma(data, period)
    std = data.rolling(window=period).std()
    upper_band = sma_line + (std * num_std)
    lower_band = sma_line - (std * num_std)

    return pd.DataFrame({"SMA": sma_line, "Upper": upper_band, "Lower": lower_band})
