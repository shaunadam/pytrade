import pull_data as pu
import pandas_ta as ta
import pandas as pd

#df = pu.getDF('2021-01-01',period = 'D', ticker = ['SU.TO','ABX.TO'])
#dfWeekly = pu.getDF('2021-01-01',period = 'W', ticker = ['SU.TO','ABX.TO'])

def DailyChecks():
    dfWeekly = pu.getDF('2021-01-01',period = 'W')

    weeklyResults = []

    for tick, df2 in dfWeekly.groupby(level=0):
        if len(df2) >52:
            df2.ta.macd(close='Adj_Close',append=True)
            df2['histDiff'] = df2['MACDh_12_26_9'].diff()
            df2.ta.ema(close='Adj_Close',length=13,append=True)
            df2['EMAdiff'] = df2['EMA_13'].diff()
            last = df2.iloc[-1,:]
            macd = last['histDiff']
            macd2 = df2['histDiff'].iloc[-2]
            ema = last['EMAdiff']
            ema2 = df2['EMAdiff'].iloc[-2]


            if macd > 0 and ema >0 and (macd2<=0 or ema2<=0):
                weeklyResults.append([tick,2])
            '''
            elif macd >0 and ema <=0:
                weeklyResults.append([tick,1])
            elif macd <=0 and ema > 0 :
                weeklyResults.append([tick,1])
            '''
    

    weeklyTicks = []
    for res in weeklyResults:
        weeklyTicks.append(res[0])

    dfDaily = pu.getDF('2022-01-01',period = 'D',ticker=weeklyTicks)
    dfDaily.set_index('Ticker',inplace=True)

    dailyResults = []

    for tick, df2 in dfDaily.groupby('Ticker'):
        if len(df2) >52:
            df2.ta.macd(close='Adj_Close',append=True)
            df2['histDiff'] = df2['MACDh_12_26_9'].diff()
            df2.ta.ema(close='Adj_Close',length=13,append=True)
            df2['EMAdiff'] = df2['EMA_13'].diff()
            last = df2.iloc[-1,:]
            macd = last['histDiff']
            macd2 = df2['histDiff'].iloc[-2]
            ema = last['EMAdiff']
            ema2 = df2['EMAdiff'].iloc[-2]
            if macd > 0 and ema >0 and (macd2<=0 or ema2<=0):
                dailyResults.append([tick,2])
    
    df = pd.DataFrame(dailyResults)
    writer = pd.ExcelWriter('out.xlsx')
    df.to_excel(writer, sheet_name='DailyScreen', index=False)
    writer.save()
    
DailyChecks()