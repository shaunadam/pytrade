# src/analysis/screener.py

import yaml
from typing import List, Dict, Any
import pandas as pd
import numpy as np
import os


class Screener:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)

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

    def screen_data(self, data: pd.DataFrame) -> pd.DataFrame:
        # Apply conditions to the data
        filtered_data = self.apply_conditions(data)

        if filtered_data.empty:
            return pd.DataFrame()

        # Calculate sorting criteria if any
        if "sort_by" in self.config:
            filtered_data = self.calculate_sort_criteria(filtered_data)

        # Keep all columns and drop duplicates on 'symbol'
        results = filtered_data.drop_duplicates(subset=["symbol"])

        # Apply sorting and limit
        results = self.sort_and_limit_results(results)

        return results

    def apply_conditions(self, data: pd.DataFrame) -> pd.DataFrame:
        # Start with all data
        filtered_data = data.copy()
        for condition in self.config["conditions"]:
            filtered_data = self.apply_condition(condition, filtered_data)
            if filtered_data.empty:
                break
        return filtered_data

    def apply_condition(
        self, condition: Dict[str, Any], data: pd.DataFrame
    ) -> pd.DataFrame:
        condition_type = condition.get("type")
        if condition_type == "indicator_comparison":
            return self.check_indicator_comparison(condition, data)
        elif condition_type == "price_action":
            return self.check_price_action(condition, data)
        elif condition_type == "volume_action":
            return self.check_volume_action(condition, data)
        elif condition_type == "indicator_value":
            return self.check_indicator_value(condition, data)
        elif condition_type == "indicator_cross":
            return self.check_indicator_cross(condition, data)
        else:
            raise ValueError(f"Unknown condition type: {condition_type}")

    def check_indicator_comparison(
        self, condition: Dict[str, Any], data: pd.DataFrame
    ) -> pd.DataFrame:
        indicator1 = condition.get("indicator1")
        indicator2 = condition.get("indicator2")
        operator = condition.get("operator")
        lookback = condition.get("lookback_periods", 1)

        # Shift data to get the lookback period
        data_shifted = data.groupby("symbol").apply(lambda x: x.tail(lookback))

        op_func = self.get_operator(operator)
        if op_func is None:
            raise ValueError(f"Invalid operator: {operator}")

        condition_met = op_func(data_shifted[indicator1], data_shifted[indicator2])

        # Filter data where the condition is True for all lookback periods
        condition_met_grouped = condition_met.groupby(data_shifted["symbol"]).all()
        valid_symbols = condition_met_grouped[condition_met_grouped].index

        return data[data["symbol"].isin(valid_symbols)]

    def check_price_action(
        self, condition: Dict[str, Any], data: pd.DataFrame
    ) -> pd.DataFrame:
        attribute = condition.get("attribute")
        operator = condition.get("operator")
        value = condition.get("value")

        op_func = self.get_operator(operator)
        if op_func is None:
            raise ValueError(f"Invalid operator: {operator}")

        latest_data = data.groupby("symbol").tail(1)
        condition_met = op_func(latest_data[attribute], value)
        valid_symbols = latest_data[condition_met]["symbol"]

        return data[data["symbol"].isin(valid_symbols)]

    def check_volume_action(
        self, condition: Dict[str, Any], data: pd.DataFrame
    ) -> pd.DataFrame:
        operator = condition.get("operator")
        lookback = condition.get("lookback_periods", 5)
        threshold = condition.get("threshold", 2.0)

        data_grouped = data.groupby("symbol")
        if operator == "increasing":
            condition_met = data_grouped["volume"].apply(
                lambda x: x.tail(lookback).diff().gt(0).all()
            )
        elif operator == "decreasing":
            condition_met = data_grouped["volume"].apply(
                lambda x: x.tail(lookback).diff().lt(0).all()
            )
        elif operator == "spike":
            condition_met = data_grouped.apply(
                lambda x: x["volume"].iloc[-1]
                >= threshold * x["volume"].iloc[-(lookback + 1) : -1].mean()
            )
        else:
            raise ValueError(f"Unknown volume action operator: {operator}")

        valid_symbols = condition_met[condition_met].index
        return data[data["symbol"].isin(valid_symbols)]

    def check_indicator_value(
        self, condition: Dict[str, Any], data: pd.DataFrame
    ) -> pd.DataFrame:
        indicator = condition.get("indicator")
        operator = condition.get("operator")
        value = condition.get("value")

        op_func = self.get_operator(operator)
        if op_func is None:
            raise ValueError(f"Invalid operator: {operator}")

        latest_data = data.groupby("symbol").tail(1)
        condition_met = op_func(latest_data[indicator], value)
        valid_symbols = latest_data[condition_met]["symbol"]

        return data[data["symbol"].isin(valid_symbols)]

    def check_indicator_cross(
        self, condition: Dict[str, Any], data: pd.DataFrame
    ) -> pd.DataFrame:
        indicator1 = condition.get("indicator1")
        direction = condition.get("direction")  # "above" or "below"
        indicator2 = condition.get("indicator2")
        value = condition.get("value")
        lookback = condition.get("lookback_periods", 1)

        def cross_condition(group):
            if len(group) < lookback + 1:
                return False
            series1 = group[indicator1]
            if indicator2:
                series2 = group[indicator2]
            elif value is not None:
                series2 = pd.Series(value, index=group.index)
            else:
                return False

            diff = series1 - series2
            diff_shifted = diff.shift(1)
            if direction == "above":
                cross = (diff > 0) & (diff_shifted <= 0)
            elif direction == "below":
                cross = (diff < 0) & (diff_shifted >= 0)
            else:
                raise ValueError(f"Invalid direction: {direction}")
            return cross.tail(lookback).any()

        condition_met = data.groupby("symbol").apply(cross_condition)
        valid_symbols = condition_met[condition_met].index

        return data[data["symbol"].isin(valid_symbols)]

    def calculate_sort_criteria(self, data: pd.DataFrame) -> pd.DataFrame:
        # Assuming we need to get the latest value for sorting
        latest_data = data.groupby("symbol").tail(1)
        return latest_data

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
