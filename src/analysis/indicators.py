import pandas as pd
import numpy as np


def sma(data, period=14, time_frame="daily"):
    """
    Calculate Simple Moving Average
    """
    if time_frame == "weekly":
        period = max(1, period // 5)
    return data.rolling(window=period).mean()


def ema(data, period=14, time_frame="daily"):
    """
    Calculate Exponential Moving Average
    """
    if time_frame == "weekly":
        period = max(1, period // 5)
    return data.ewm(span=period, adjust=False).mean()


def rsi(data, period=14, time_frame="daily"):
    """
    Calculate Relative Strength Index
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(data, fast_period=12, slow_period=26, signal_period=9, time_frame="daily"):
    """
    Calculate Moving Average Convergence Divergence (MACD)
    """
    # if time_frame == "weekly":
    #    fast_period = max(1, fast_period // 5)
    #    slow_period = max(1, slow_period // 5)
    #    signal_period = max(1, signal_period // 5)
    fast_ema = ema(data, fast_period, time_frame=time_frame)
    slow_ema = ema(data, slow_period, time_frame=time_frame)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_period, time_frame=time_frame)
    macd_histogram = macd_line - signal_line

    return pd.DataFrame(
        {"MACD": macd_line, "Signal": signal_line, "Histogram": macd_histogram}
    )


def bollinger_bands(data, period=20, num_std=2, time_frame="daily"):
    """
    Calculate Bollinger Bands
    """
    if time_frame == "weekly":
        period = max(1, period // 5)
    sma_line = sma(data, period, time_frame=time_frame)
    std = data.rolling(window=period).std()
    upper_band = sma_line + (std * num_std)
    lower_band = sma_line - (std * num_std)

    return pd.DataFrame({"SMA": sma_line, "Upper": upper_band, "Lower": lower_band})
