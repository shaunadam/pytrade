# Project To-Do Overview

## 1. **Project Restructure**
1. **Remove Dash/Plotly & Unused Files**  
   - Eliminate the entire dashboard and callback logic.  
   - Delete or comment out any modules purely supporting Dash (callbacks, layout components, etc.).  
   - Prune files that are no longer necessary (e.g., YAML screener configs, leftover assets).

2. **Simplify Folder Structure**  
   - Consider collapsing the `visualization` directory if you plan to generate only simple HTML/plots without an interactive framework.  
   - Combine or rename modules as needed (for instance, unify data fetch and indicator logic into fewer classes).

3. **Improve Code Traceability**  
   - Review each class (`DataService`, `DatabaseManager`, etc.) to confirm it’s really needed.  
   - Keep common functionality (like “screeners” or “indicator calculations”) in a single, clear module.  
   - Avoid partial duplication of logic.

---

## 2. **Screening with Python-Only Definitions**
1. **Remove YAML Config Approach**  
   - Delete the YAML screener definitions (`.yaml`) and their loader code.  
   - Convert screener logic directly into Python classes or functions.

2. **Define a Pythonic Screener Interface**  
   - For example:
     ```python
     def rsi_oversold_rebound(data, rsi_threshold=30):
         # returns True/False for each row
     ```
   - Encapsulate “AND/OR” condition logic within the function or via function chaining.

3. **Keep It Modular**  
   - Example:
     ```python
     def run_screeners(data, screeners=[rsi_oversold_rebound, macd_bullish_cross]):
         # Apply each screener to `data`
         # Return a summary or DataFrame with results
     ```
   - Verify efficiency for a few thousand symbols in DataFrames.

---

## 3. **Generate a Simple Report (HTML/Static Plots)**
1. **Create a Summary Report**  
   - For each screener, show a table of matching symbols.  
   - Possibly include overall stats (e.g., how many tickers passed each screener).  
   - Output to an HTML file via, for instance, `pandas.DataFrame.to_html()` or a Jinja2 template.

2. **Optional Plots**  
   - Use Seaborn/Matplotlib to create PNG charts, then embed via `<img>` tags.  
   - Keep them static (no interactive hover/zoom).

3. **Combine Multiple Screeners**  
   - If you run more than one screener, produce separate sections or tables in the same report.

---

## 4. **Basic Backtesting**
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

## 5. **Optimize Query Performance**
1. **Investigate Slow Updates**  
   - Profile indicator updates (are we doing row-by-row inserts?).  
   - Check transaction commit frequency and possibly use batch inserts.

2. **Vectorize Calculations**  
   - Ensure indicator calculations use vectorized pandas/NumPy (avoid Python loops).

3. **Query Tuning**  
   - Limit data fetching to only the needed date range.  
   - Validate indexes on critical columns in PostgreSQL.

4. **Potential Timeseries Libraries**  
   - Consider solutions like Polars or DuckDB for partial analytics.  
   - Cache recently fetched data in DataFrames to avoid repeated queries.

---

## 6. **(Future) Containerization / Docker Compose**
1.
