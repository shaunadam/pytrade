import os
import json
import requests

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "stocks.db")


# Data
def load_tsx_symbols():
    url = "https://www.tsx.com/json/company-directory/search/tsx/%5E*"
    response = requests.get(url)
    data = response.json()

    symbols = []
    for company in data["results"]:
        symbol = company["symbol"]
        # Add '.TO' suffix if not already present
        if not symbol.endswith(".TO"):
            symbol += ".TO"
        symbols.append(symbol)

    return symbols


# TSX_SYMBOLS = load_tsx_symbols()
# TSX_SYMBOLS = load_tsx_symbols()[0:10]
TSX_SYMBOLS = ["SU.TO"]

START_DATE = "2024-10-10"
END_DATE = "2024-12-31"
