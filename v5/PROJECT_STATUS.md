# TSX Swing Trading Project

## Current Status
- Basic project structure set up
- SQLite database initialized with schema for stocks and daily data
- Data fetching implemented using yfinance for TSX symbols
- Simple CLI interface to update stock data

## Project Structure
```
project_root/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── fetcher.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── indicators.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── init_db.py
│   ├── backtesting/
│   │   ├── __init__.py
│   │   └── strategies.py
│   └── visualization/
│       ├── __init__.py
│       └── dashboard.py
│
├── tests/
│   ├── __init__.py
│   ├── test_data.py
│   ├── test_analysis.py
│   └── test_backtesting.py
│
├── config.py
├── main.py
├── requirements.txt
├── .gitignore
└── PROJECT_STATUS.md

```

## Completed Tasks
- [x] Project folder structure
- [x] Database initialization script (src/database/init_db.py)
- [x] Configuration file (config.py)
- [x] Data fetcher class (src/data/fetcher.py)
- [x] Main script for data updates (main.py)
- [x] .gitignore file
- [x] Create module for technical indicators (src/analysis/indicators.py)

## Next Steps

- [ ] Develop Plotly Dash frontend for data visualization (src/visualization/dashboard.py)
- [ ] Implement backtesting module (src/backtesting/strategies.py)
- [ ] Optimize data storage and retrieval
- [ ] Write unit tests (in the tests/ directory)

## Overall Goals
1. Minimize time spent on stock screening
2. Create custom screeners for TSX stocks
3. Implement and backtest swing trading strategies
4. Develop a user-friendly interface for strategy visualization and analysis

## Tech Stack
- Python
- SQLite
- SQLAlchemy
- yfinance
- Plotly Dash (planned)

## Key Files
- `config.py`: Contains configuration variables like database path, stock symbols, and date ranges
- `main.py`: Entry point for running data updates
- `src/database/init_db.py`: Initializes the SQLite database and defines the schema
- `src/data/fetcher.py`: Handles fetching and updating stock data
- `requirements.txt`: Lists all Python dependencies for the project