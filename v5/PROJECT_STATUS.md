# TSX Swing Trading Project

## Current Status
- Basic project structure set up
- SQLite database initialized with schema for stocks and daily data
- Data fetching implemented using yfinance for TSX symbols
- Technical indicators calculation implemented (SMA, EMA, RSI, MACD, Bollinger Bands)
- Basic Plotly Dash dashboard created for data visualization
- Command-line interface for updating data, testing indicators, and running the dashboard

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
- [x] Implement basic Plotly Dash dashboard (src/visualization/dashboard.py)
- [x] Add command-line interface for different operations

## Recent Updates
- Implemented a basic Plotly Dash dashboard for visualizing stock data
- Added technical indicators (SMA, EMA) to the dashboard
- Implemented data caching to improve dashboard performance
- Added date range selection functionality to the dashboard
- Updated main.py to use argparse for better control over operations

## Next Steps
- [ ] Setup tabs to make dash app look nice and setup for future expansion. Use dark theme.
- [ ] Allow user to pick indicators. Add a volume chart below the price candlesticks chart and force the xaxis to stay aligned.
- [ ] Add more technical indicators to the dashboard (RSI, MACD, Bollinger Bands)
- [ ] Implement backtesting module (src/backtesting/strategies.py)
- [ ] Create custom screeners for TSX stocks
- [ ] Develop and test swing trading strategies
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
- Plotly Dash
- Pandas

## Key Files
- `config.py`: Contains configuration variables like database path, stock symbols, and date ranges
- `main.py`: Entry point for running data updates, testing indicators, and launching the dashboard
- `src/database/init_db.py`: Initializes the SQLite database and defines the schema
- `src/data/fetcher.py`: Handles fetching and updating stock data
- `src/analysis/indicators.py`: Calculates technical indicators
- `src/visualization/dashboard.py`: Implements the Plotly Dash dashboard
- `requirements.txt`: Lists all Python dependencies for the project

## Usage
To run different parts of the project:
1. Update stock data: `python main.py --update`
2. Test indicators: `python main.py --test`
3. Run the dashboard: `python main.py --dashboard`

## Known Issues
- Some technical indicators may need refinement in calculation or display