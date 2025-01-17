from abc import ABC, abstractmethod
import pandas as pd


class BaseScreener(ABC):
    @abstractmethod
    def apply(self, data: pd.DataFrame) -> pd.Series:
        pass


class RSIOversoldScreener(BaseScreener):
    def __init__(self, threshold: float = 30):
        self.threshold = threshold

    def apply(self, data: pd.DataFrame) -> pd.Series:
        return data["RSI"] < self.threshold


class MACDBullishCrossScreener(BaseScreener):
    def apply(self, data: pd.DataFrame) -> pd.Series:
        return (data["MACD"] > data["MACD_Signal"]) & (
            data["MACD"].shift(1) <= data["MACD_Signal"].shift(1)
        )


class CompositeScreener(BaseScreener):
    def __init__(self, screeners, mode="AND"):
        self.screeners = screeners
        self.mode = mode.upper()

    def apply(self, data: pd.DataFrame) -> pd.Series:
        results = [screener.apply(data) for screener in self.screeners]
        if self.mode == "AND":
            return pd.concat(results, axis=1).all(axis=1)
        elif self.mode == "OR":
            return pd.concat(results, axis=1).any(axis=1)
        else:
            raise ValueError("Mode must be 'AND' or 'OR'")
