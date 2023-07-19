import pull_data as pu

#pu.refreshTSX("1y")

test = pu.getDF("2022-12-01",'W','PBD.TO')
print(test)

