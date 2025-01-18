# Project To-Do Overview

## 1. **Generate a Simple Report (HTML/Static Plots)**
1. **Create a Summary Report**  
   - For each screener, show a table of matching symbols.  
   - Possibly include overall stats (e.g., how many tickers passed each screener).  
   - Output to an HTML file via, for instance, `pandas.DataFrame.to_html()` or a Jinja2 template.

2. **Optional Plots**  
   - Use Seaborn/Matplotlib to create PNG charts, then embed via `<img>` tags.  
   - Keep them static (no interactive hover/zoom).

3. **Combine Multiple Screeners**  
   - If you run more than one screener, produce separate sections or tables in the same report.


## 2. **Basic Backtesting**
1. **Implement Simple Buy/Sell Logic**  
   - Example: “buy when RSI < 30, sell when RSI > 50.”  
   - Track trade P/L and final returns.

2. **Collect Key Metrics**  
   - e.g., total return, max drawdown, number of trades, average win/loss.  
   - Store in a dictionary or DataFrame.

3. **Minimal Report**  
   - Summarize backtest results in the same HTML file or a separate one.  
   - Possibly one PnL chart over time.

4. **Future Extensibility**  
   - Keep code open to advanced position management or multiple time frames later.

---

## 3. **(Future) Containerization / Docker Compose**
should I use a python ta library instead of calculating my own indicators? maybe it's fine this way?
