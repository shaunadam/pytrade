# Project To-Do Overview

## 2. **Develop screeners in python**
1. **Improve compositescreener so add flexibility (and/or nested combinations)**
   - Need to abstract the import out of main.py so I don't have to keep adjusting it. Own file?
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
