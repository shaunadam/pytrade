import os
import json
import requests

# Database
DB_USER = "shaun"
DB_PASSWORD = "ss341122"
DB_HOST = "localhost"  # Use 'db' if using Docker Compose; otherwise, 'localhost'
DB_PORT = "5432"
DB_NAME = "pytrade"

# SQLAlchemy Database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


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


TSX_SYMBOLS = load_tsx_symbols()
# TSX_SYMBOLS = load_tsx_symbols()[0:10]
# TSX_SYMBOLS = ["SU.TO", "ABX.TO"]

START_DATE = "2025-01-10"
END_DATE = "2025-12-31"
