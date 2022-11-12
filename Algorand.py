import yfinance as yf
from matplotlib import pyplot as plt
from pandas import DataFrame,Timestamp

def download(period='5d'):
    algo = yf.download('algo-usd',period=period,interval='1m')
    algo.pop('Volume')
    algo.pop('Adj Close')
    algo = algo.reset_index()

    return algo
    
def percent_col(df,col):
    percent = [0]
    for i,row in df.iterrows():
        if i > 0:
            new = row[col]
            old = df.iloc[i-1][col]
            if old != 0: percent += [100*(new-old)/old]
            else: percent += [0]
    df[f'delta {col}'] = percent
    return df, f'delta {col}'

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
    for i,row in df.iterrows():
        row['Datetime'] = row['Datetime'].tz_convert(tz)
    return df

def plot():
    algo = download('5d')
    algo,long = moving_avg(algo,240)
    algo,short = moving_avg(algo,20)

    algo,delta = delta_col(algo,short)

    algo = algo[-60*5:]
    ot = algo.loc[algo[long] > 0]
    t = algo.loc[algo[short] > 0]

    plt.subplot(1,2,1)
    plt.plot(algo.index,algo['Close'])
    plt.plot(ot.index,ot[long],color='orange')
    plt.plot(t.index,t[short],color='green')

    plt.subplot(1,2,2)
    x, y = [list() for _ in range(2)]
    for i,row in algo.iterrows():
        if i%1 == 0:
            x += [row.name]
            y += [row[delta]]
    plt.plot(x,y)


    print(algo)
    plt.show()

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

def smooth_col(df,col,smooth=2):
    avg = [0 for _ in range(smooth)]
    for i,row in df[smooth:].iterrows():
        avg += [df[col][i-smooth:i].mean()]

    newCol = f'{col} smooth'
    df[newCol] = avg
    return df,newCol

def ind_avg(df,col):
    holding = False
    ind = ['na']
    for i,row in df[1:].iterrows():
        if not holding:
            below = df[col][i-1] < 0
            cross = row[col] > 0 
            if below and cross:
                holding = True
                ind += ['buy']
            else:
                ind += ['na']
        elif holding:
            positive = row[col] > 0
            peak = df[col][i-1] > row[col]
            if positive and peak:
                holding = False
                ind += ['sell']
            else:
                ind += ['hold']
    
    column_name = f'{col} ind'
    df[column_name] = ind
    return df, column_name

if __name__ == '__main__':
    algo = download('5d')
    algo,short = moving_avg(algo,40)
    algo,delta = delta_col(algo,short)
    algo,smooth = smooth_col(algo,delta,12)
    algo,ind = ind_avg(algo,smooth)

    buy = (algo.loc[algo[ind] == 'buy']).reset_index()
    sell = (algo.loc[algo[ind] == 'sell']).reset_index()

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