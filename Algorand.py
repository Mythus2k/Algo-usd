import yfinance as yf
from matplotlib import pyplot as plt
from pandas import DataFrame,concat,Timedelta

def download(period='5d'):
    algo = yf.download('algo-usd',period=period,interval='1m')
    algo.pop('Volume')
    algo.pop('Adj Close')
    algo = algo.reset_index()

    return algo

def point_col(df,timeframe=60):
    points = [0 for _ in range(timeframe)]
    for i in range(timeframe,len(df)):
        sec = df[i-timeframe:i]
        high = sec['High'].max()
        low = sec['Low'].min()
        close = sec['Close'][i-1]

        points += [100*(close-low)/(high-low)]

    df['point'] = points
    return df

def moving_avg(df,history=120):
    avg = [0 for _ in range(history)]
    for i,row in df[history:].iterrows():
        avg += [df[i-history:i]['Close'].mean()]

    df[f'{history} avg'] = avg
    return df, f'{history} avg'

def adj_tz(df,tz='US/Eastern'):
    Datetime = []
    for i,row in df.iterrows():
        Datetime += [row['Datetime'] - Timedelta('5 hours')]

    df['Datetime'] = Datetime
    return df

def gap_col(df,long,short):
    l = df[long]
    s = df[short]

    diff = [s[i] - l[i] for i in range(len(l))]

    df[f'gap {long} v {short}'] = diff
    return df, f'gap {long} v {short}'

def delta_col(df,col):
    delta = [0]
    c = df[col]
    delta += [c[i] - c[i-1] for i in range(1,len(c))]
    df[f'delta {col}'] = delta
    return df,f'delta {col}'

def smooth_col(df,col,smooth=2,newCol=False):
    avg = [0 for _ in range(smooth)]
    for i,row in df[smooth:].iterrows():
        avg += [df[col][i-smooth:i].mean()]

    if newCol:
        newCol = f'{col} smooth'
        df[newCol] = avg
        return df,newCol
    else:
        df[col] = avg
        return df,col

def ind_avg(df,indCol):
    holding = False
    ind = ['na']
    for i,row in df[1:].iterrows():
        if not holding:
            one = row[indCol] > df[indCol][i-1]
            two = row[indCol] < row['Close']
            if one and two:
                holding = True
                enter = row['Close']
                ind += ['buy']
            else:
                ind += ['na']
        elif holding:
            one = row[indCol] < df[indCol][i-1]
            take = ((row['Close'] - enter)/enter) > .003
            if one or take:
                holding = False
                ind += ['sell']
            else:
                ind += ['hold']
    
    column_name = f'{indCol} ind'
    df[column_name] = ind
    return df, column_name

def meth_One():
    algo = download('5d')
    # moving avg: 60,20 smoothing: 10,10
    algo,short = moving_avg(algo,60)
    algo,delta = delta_col(algo,short)
    algo,smooth = smooth_col(algo,delta,8)
    algo,ind = ind_avg(algo,short)

    buy = (algo.loc[algo[ind] == 'buy'])
    sell = (algo.loc[algo[ind] == 'sell'])

    viewslot = 60*8
    plotting = algo[-viewslot:]
    b = plotting.loc[plotting[ind] == 'buy']
    s = plotting.loc[plotting[ind] == 'sell']
    plt.subplot(2,1,2)
    plt.plot(plotting.index,plotting[smooth])
    plt.plot(plotting.index,[0 for _ in range(len(plotting.index))],
    color='gray')

    plt.subplot(2,1,1)
    plt.plot(plotting.index,plotting['Close'])
    a = plotting.loc[plotting[short] > 0]
    plt.plot(a.index,a[short],color='orange')
    plt.scatter(b.index,b['Close'],marker='x',color='green')
    plt.scatter(s.index,s['Close'],marker='x',color='red')

    buy = buy.reset_index()
    sell = sell.reset_index()
    perf = list()
    holding = list()
    for i in range(len(sell)):
        perf += [100*(sell['Close'][i]-buy['Close'][i])/buy['Close'][i]]
        holding += [(sell['Datetime'][i]-buy['Datetime'][i]).seconds/60]

    perf = DataFrame({'perf':perf,'hold':holding})
    print(f'performance: {perf["perf"].sum():4.4}%')
    print(f'  trade avg: {perf["perf"].mean():4.4}%')
    print(f'        std: {perf["perf"].std():4.4}%')
    print(f'     trades: {perf["perf"].count()}')
    print(f' trade time: {perf["hold"].mean():4.4}')
    print(f'  trade dev: {perf["hold"].std():4.4}')

    print(algo.iloc[-1][ind])
    plt.show()

def buy_ind(df,mvg_avg,dmvg_avg,lmvg_avg):
    algo = df
    short = mvg_avg
    _short = dmvg_avg
    long = lmvg_avg
    # buy indicator - crossing
    holding = False
    counter = 0
    ind = ['na']
    for i,row in algo[1:].iterrows():
        if holding:
            holding = False
            counter = 10
            ind += ['na']
        elif counter == 0 and not holding:
            prev = algo[_short][i-1] < 0
            cross = row[_short] > 0
            up = row[long] > row[short]
            if prev and cross and up:
                holding = True
                ind += ['buy']
            else:
                ind += ['na']
        else:
            counter -= 1
            ind += ['na']

    algo['buy'] = ind
    return algo,'buy'

def sell_ind(df,mvg_avg,dmvg_avg,lmvg_avg):
    algo = df
    short = mvg_avg
    _short = dmvg_avg
    long = lmvg_avg
    # buy indicator - crossing
    holding = False
    counter = 0
    ind = ['na']
    for i,row in algo[1:].iterrows():
        if holding:
            holding = False
            counter = 10
            ind += ['na']
        elif counter == 0 and not holding:
            prev = algo[_short][i-1] > 0
            cross = row[_short] < 0
            up = row[long] < row[short]
            if prev and cross and up:
                holding = True
                ind += ['sell']
            else:
                ind += ['na']
        else:
            counter -= 1
            ind += ['na']

    algo['sell'] = ind
    return algo,'sell'

def find_profitability(df,printStats=False):
    buys = df.loc[df['buy'] == 'buy']
    sells = df.loc[df['sell'] == 'sell']
    mixed = concat([buys,sells]).sort_index().reset_index()

    holds = dict()
    perform = []
    times = []
    for i,row in mixed.iterrows():
        if row['buy'] == 'buy':
            holds[row.name] = row
        elif row['sell'] == 'sell':
            close = row['Close']
            etime = row['Datetime']
            for b in holds.values():
                enter = b['Close']
                time = b['Datetime']
                perform += [100*(close-enter)/enter]
                times += [(etime-time).seconds/60]
            holds = dict()
    
    
    p = (DataFrame({0:perform,1:times}))
    if printStats:
        print(f'sum : {p[0].sum():.4}%')
        print(f'mean: {p[0].mean():.4}%')
        print(f'std : {p[0].std():.4}%')
        print(f'min : {p[0].min():.4}%')
        print(f'max : {p[0].max():.4}%')

    return p

def main(prints=False):
    algo = download()
    algo = adj_tz(algo)

    algo,long = moving_avg(algo,240)

    algo,short = moving_avg(algo,60)

    algo,_short = delta_col(algo,short)
    algo,_short = smooth_col(algo,_short,8)
    
    algo,buy = buy_ind(algo,short,_short,long)
    algo,sell = sell_ind(algo,short,_short,long)

    buys = algo.loc[algo['buy'] == 'buy']
    sells = algo.loc[algo['sell'] == 'sell']

    m = concat([buys,sells,algo[-1:]]).sort_index()
    print(m[['Datetime','Close','buy','sell']][-5:])
    m.to_csv('algo.csv')

    if prints:
        p = find_profitability(algo,True)

        algo = algo[-60*12:]
        x = algo.index

        plt.subplot(2,1,1)
        plt.plot(x,algo['Close'])
        plt.plot(x,algo[short],color='green')
        plt.plot(x,algo[long],color='orange')
        plt.scatter(buys.index,buys['Close'],marker='x',color='green')
        plt.scatter(sells.index,sells['Close'],marker='x',color='red')

        plt.subplot(2,1,2)
        plt.plot(x,algo[_short],color='green')
        plt.plot(x,[0 for _ in range(len(x))],color='gray')
        plt.show()

if __name__ == '__main__':
    main()