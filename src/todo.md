

## Overall Goals
1. Minimize time spent on stock screening
2. Create custom screeners for TSX stocks
3. Implement and backtest swing trading strategies
4. Develop a user-friendly interface for strategy visualization and analysis


**To do**
- Need to deal with weekly data as well as daily
- Need weekly indicators
- Need strategies to support multiple time frames. 
- Need to ask chat GPT about general functions of this kind of algo trading platform. Could try referencing functions within quantstrat
- Develop config based backtesting system. Includes order creation (buy/sell), position siding, and needs to define order entry, order exit points. Need to keep track of transactions made and standard metrics like drawdown, profit, etc. 
- Write unit tests (in the tests/ directory)

**Status**
- Weekly data is built from daily. Needs to respect the symbols and date range being refreshed (instead of recomputing for all symbols and dates), worked great for initial population but it's slow on update. Need to offset the start date like was done for daily indicators.

- daily indicators insertion failed.

[SQL: DELETE FROM technical_indicators WHERE technical_indicators.stock_id = ? AND technical_indicators.date >= ? AND technical_indicators.time_frame = ?]
[parameters: (1628, '2023-10-11', 'daily')]
(Background on this error at: https://sqlalche.me/e/20/e3q8)

- haven't tested strategies yet.