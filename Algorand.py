import yfinance as yf
from matplotlib import pyplot as plt
from pandas import DataFrame,Timestamp

def download(period='5d'):
    """
    timeframe : int
        in minutes, history included in point column
    """
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

def plot_price(df,period=[240,0]):
    df = df[-period[0]:-period[1]]
    x = df.index

    plt.plot(x,df['Close'])
    plt.plot(x,df['120 avg'])
    plt.plot(x,df['20 avg'])
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

if __name__ == '__main__':
    algo = download('5d')
    algo,long = moving_avg(algo,240)
    algo,short = moving_avg(algo,20)

    algo,diff = gap_col(algo,long,short)
    algo,delta = delta_col(algo,diff)

    algo = algo[-60*8:]
    ot = algo.loc[algo[long] > 0]
    t = algo.loc[algo[short] > 0]

    plt.subplot(1,3,1)
    plt.plot(algo.index,algo['Close'])
    plt.plot(ot.index,ot[long],color='orange')
    plt.plot(t.index,t[short],color='green')

    plt.subplot(1,3,2)
    plt.plot(algo.index,algo[diff])

    plt.subplot(1,3,3)
    plt.plot(algo.index,algo[delta])
    plt.show()