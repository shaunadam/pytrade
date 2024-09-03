


import pull_data as pu
import const as c
import TAtransforms as ta
import pendulum

#pu.refreshTSX("3mo",secs=['ABX.TO','SU.TO'])
#test = pu.getDF("2022-12-01",'W','PBD.TO')


def stocksUpdate():
    pu.refreshTSX(c.PERIOD)
    

def taUpdate():
    now = pendulum.now()
    start = now.subtract(years=c.TAYEARS).strftime('%Y-%m-%d')
    ta.updateTA(start)

mode = 1
if __name__ == '__main__':
    
    if mode == 1:
        print('Stock update only')
        stocksUpdate()
        print('Stock update complete')
    elif mode == 2:
        print('TA update only')
        taUpdate()
        print('TA update complete')
    else:
        print('Stock and TA udpate')
        print('Starting stock  update')
        stocksUpdate()
        print('Finished stock update')
        print('Starting TA update')
        taUpdate()
        print('Finished TA update')


    

