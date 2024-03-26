


import pull_data as pu
import const as c
import TAtransforms as ta
import pendulum

#pu.refreshTSX("3mo",secs=['ABX.TO','SU.TO'])
#test = pu.getDF("2022-12-01",'W','PBD.TO')
pu.refreshTSX(c.PERIOD)
now = pendulum.now()

start = now.subtract(years=c.TAYEARS).strftime('%Y-%m-%d')
ta.updateTA(start)

