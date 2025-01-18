from abc import ABC, abstractmethod
import pandas as pd

screener_registry = {}


def register_screener(name):
    def decorator(cls):
        screener_registry[name.lower()] = cls
        return cls

    return decorator


class BaseScreener(ABC):
    @abstractmethod
    def apply(self, data: pd.DataFrame) -> pd.Series:
        pass


@register_screener("rsi_oversold")
class RSIOversoldScreener(BaseScreener):
    def __init__(self, threshold: float = 30):
        self.threshold = threshold

    def apply(self, data: pd.DataFrame) -> pd.Series:
        return data["RSI"] < self.threshold


@register_screener("macd_bullish_cross")
class MACDBullishCrossScreener(BaseScreener):
    def apply(self, data: pd.DataFrame) -> pd.Series:
        return (data["MACD"] > data["MACD_Signal"]) & (
            data["MACD"].shift(1) <= data["MACD_Signal"].shift(1)
        )


@register_screener("bollinger_breakout")
class BollingerBreakoutScreener(BaseScreener):
    def apply(self, data: pd.DataFrame) -> pd.Series:
        return data["close"] > data["BB_Upper"]


@register_screener("golden_cross")
class GoldenCrossScreener(BaseScreener):
    def apply(self, data: pd.DataFrame) -> pd.Series:
        return (data["SMA50"] > data["SMA200"]) & (
            data["SMA50"].shift(1) <= data["SMA200"].shift(1)
        )


# Composite Screener
class CompositeScreener(BaseScreener):
    def __init__(self, screener_names, mode="AND"):
        self.mode = mode.upper()
        self.screeners = self._initialize_screeners(screener_names)

    def _initialize_screeners(self, screener_names):
        screeners = []
        for name in screener_names:
            screener_class = screener_registry.get(name.lower())
            if screener_class:
                screeners.append(screener_class())
            else:
                print(f"Warning: Screener '{name}' not found in the registry.")
        return screeners

    def apply(self, data: pd.DataFrame) -> pd.Series:
        results = [screener.apply(data) for screener in self.screeners]
        combined_result = pd.concat(results, axis=1)
        if self.mode == "AND":
            return combined_result.all(axis=1)
        elif self.mode == "OR":
            return combined_result.any(axis=1)
        else:
            raise ValueError("Mode must be 'AND' or 'OR'")
