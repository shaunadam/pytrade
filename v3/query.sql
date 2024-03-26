SELECT Exchange, Ticker, count(AdjClose), min(Date)
FROM marketData group by Exchange, Ticker having count(MACD)=0 order by Ticker;