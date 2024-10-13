# TSX Swing Trading Project
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

## Usage
To run different parts of the project:
1. Update stock data: `python main.py --update`
2. Test indicators: `python main.py --test`
3. Run the dashboard: `python main.py --dashboard`

## Known Issues