import os

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "stocks.db")

# Data
TSX_SYMBOLS = [
    "SHOP.TO",
    "RY.TO",
    "TD.TO",
    "ENB.TO",
    "CNR.TO",
]  # Add more TSX symbols as needed
START_DATE = "2020-01-01"
END_DATE = "2024-12-31"

# API
ALPHA_VANTAGE_API_KEY = (
    "your_alpha_vantage_api_key_here"  # If you decide to use Alpha Vantage
)
