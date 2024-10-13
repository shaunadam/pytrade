import yaml
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from src.data.fetcher import StockDataFetcher
import os


class Screener:
    def __init__(self, config_path: str, data_fetcher: StockDataFetcher):
        self.config = self.load_config(config_path)
        self.data_fetcher = data_fetcher

    def load_config(self, config_name: str) -> Dict[str, Any]:
        # Construct the path to the analysis folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, f"{config_name}.yaml")

        # Check if the file exists
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Load and return the config
        with open(config_path, "r") as file:
            return yaml.safe_load(file)

    def screen(
        self, symbols: List[str], start_date: str, end_date: str
    ) -> pd.DataFrame:
        results = []
        for symbol in symbols:
            data = self.data_fetcher.get_stock_data_with_indicators(
                symbol, start_date, end_date
            )
            if not data.empty:
                if self.apply_conditions(data):
                    results.append(
                        {"symbol": symbol, **self.calculate_sort_criteria(data)}
                    )

        results_df = pd.DataFrame(results)
        return self.sort_and_limit_results(results_df)

    def apply_conditions(self, data: pd.DataFrame) -> bool:
        for condition in self.config["conditions"]:
            if not self.check_condition(condition, data):
                return False
        return True

    def check_condition(self, condition: Dict[str, Any], data: pd.DataFrame) -> bool:
        try:
            if condition["type"] == "indicator_comparison":
                return self.check_indicator_comparison(condition, data)
            elif condition["type"] == "price_action":
                return self.check_price_action(condition, data)
            elif condition["type"] == "volume_action":
                return self.check_volume_action(condition, data)
            elif condition["type"] == "indicator_value":
                return self.check_indicator_value(condition, data)
            else:
                raise ValueError(f"Unknown condition type: {condition['type']}")
        except (KeyError, IndexError, TypeError) as e:
            # Log the exception if necessary
            # For example: logging.warning(f"Condition check failed for {condition}: {e}")
            return False

    def check_indicator_comparison(
        self, condition: Dict[str, Any], data: pd.DataFrame
    ) -> bool:
        indicator1 = condition.get("indicator1")
        indicator2 = condition.get("indicator2")
        operator = condition.get("operator")
        lookback = condition.get("lookback_periods", 1)

        # Validate presence of indicators
        if indicator1 not in data.columns or indicator2 not in data.columns:
            return False

        # Validate sufficient data for lookback
        if len(data) < lookback:
            return False

        ind1 = data[indicator1].tail(lookback)
        ind2 = data[indicator2].tail(lookback)
        op = self.get_operator(operator)
        if op is None:
            raise ValueError(f"Invalid operator: {operator}")

        return op(ind1, ind2).all()

    def check_price_action(self, condition: Dict[str, Any], data: pd.DataFrame) -> bool:
        attribute = condition.get("attribute")
        operator = condition.get("operator")
        value = condition.get("value")

        # Validate presence of attribute
        if attribute not in data.columns:
            return False

        # Validate sufficient data
        if len(data) < 1:
            return False

        price = data[attribute].iloc[-1]
        op = self.get_operator(operator)
        if op is None:
            raise ValueError(f"Invalid operator: {operator}")

        return op(price, value)

    def check_volume_action(
        self, condition: Dict[str, Any], data: pd.DataFrame
    ) -> bool:
        operator = condition.get("operator")
        lookback = condition.get("lookback_periods", 5)

        # Validate presence of volume
        if "volume" not in data.columns:
            return False

        # Validate sufficient data for lookback
        if len(data) < (lookback + 1):  # +1 because diff reduces length by 1
            return False

        volume = data["volume"]
        if operator == "increasing":
            return (volume.diff().tail(lookback) > 0).all()
        elif operator == "decreasing":
            return (volume.diff().tail(lookback) < 0).all()
        else:
            raise ValueError(f"Unknown volume action operator: {operator}")

    def check_indicator_value(
        self, condition: Dict[str, Any], data: pd.DataFrame
    ) -> bool:
        indicator = condition.get("indicator")
        operator = condition.get("operator")
        value = condition.get("value")

        # Validate presence of indicator
        if indicator not in data.columns:
            return False

        # Validate sufficient data
        if len(data) < 1:
            return False

        indicator_value = data[indicator].iloc[-1]
        op = self.get_operator(operator)
        if op is None:
            raise ValueError(f"Invalid operator: {operator}")

        return op(indicator_value, value)

    def calculate_sort_criteria(self, data: pd.DataFrame) -> Dict[str, float]:
        criteria = {}
        for sort_item in self.config.get("sort_by", []):
            attribute = sort_item["attribute"]
            if attribute in data.columns:
                criteria[attribute] = data[attribute].iloc[-1]
        return criteria

    def sort_and_limit_results(self, results_df: pd.DataFrame) -> pd.DataFrame:
        if results_df.empty:
            return results_df
        if "sort_by" in self.config:
            sort_columns = [item["attribute"] for item in self.config["sort_by"]]
            sort_ascending = [
                item["order"] == "ascending" for item in self.config["sort_by"]
            ]
            results_df = results_df.sort_values(
                by=sort_columns, ascending=sort_ascending
            )

        if "limit" in self.config:
            results_df = results_df.head(self.config["limit"])

        return results_df

    @staticmethod
    def get_operator(op_string: str):
        ops = {
            ">": np.greater,
            "<": np.less,
            ">=": np.greater_equal,
            "<=": np.less_equal,
            "==": np.equal,
            "!=": np.not_equal,
        }
        return ops.get(op_string)


# Example usage:
# screener = Screener("path_to_config.yaml", data_fetcher)
# results = screener.screen(symbols, start_date, end_date)
