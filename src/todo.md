

## Overall Goals
1. Minimize time spent on stock screening
2. Create custom screeners for TSX stocks
3. Implement and backtest swing trading strategies
4. Develop a user-friendly interface for strategy visualization and analysis


**To do**
- need to speed up data updates now that we're on postgres. Do queries or overall flow need to change?
- Need strategies to support multiple time frames. 
- Need to ask chat GPT about general functions of this kind of algo trading platform. Could try referencing functions within quantstrat
- Develop config based backtesting system. Includes order creation (buy/sell), position siding, and needs to define order entry, order exit points. Need to keep track of transactions made and standard metrics like drawdown, profit, etc. 
- Write unit tests (in the tests/ directory)

**Status**

- haven't tested strategies yet.