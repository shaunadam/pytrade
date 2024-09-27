# TSX Swing Trading Project

## Current Status
- Basic project structure set up
- SQLite database initialized with schema for stocks and daily data
- Data fetching implemented using yfinance for TSX symbols
- Technical indicators calculation implemented (SMA, EMA, RSI, MACD, Bollinger Bands)
- Basic Plotly Dash dashboard created for data visualization
- Command-line interface for updating data, testing indicators, and running the dashboard

## Recent Updates
- Added date range selection functionality to the dashboard
- Updated main.py to use argparse for better control over operations
- Designed a new structure for the dashboard with tabs for different functionalities
- Planned implementation of config-driven development for backtesting and screening
- Refactored the Dash app to use the new tabbed structure
- Add a Utility tab for overriding the start date / end date and a button to manually tigger downloading stock data.

## Next Steps
- [ ] Implement config-driven development for screening criteria, and backtesting strategies
- [ ] Create separate components for each major feature (e.g., StockChart, IndicatorPanel, Screener)
- [ ] Implement lazy loading for tab content using callbacks
- [ ] Use dcc.Store for basic state management (selected stock, date range)
- [ ] Develop the Stock Screening tab functionality
- [ ] Develop the Backtesting tab functionality
- [ ] Add more technical indicators to the dashboard (RSI, MACD, Bollinger Bands)
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