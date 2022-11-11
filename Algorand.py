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

def diff_col(df,long,short):
    l = algo.loc[algo[long] > 0]
    diff = [0 for _ in range(len(df)-len(l))]
    for i, row in l.iterrows():
        diff += [df[i][short]-df[i][long]]

    df[f'{long:3} vs {short:3}'] = diff
    return df, f'{long:3} vs {short:3}'

if __name__ == '__main__':
    algo = download('5d')
    algo,long = moving_avg(algo,120)
    algo,short = moving_avg(algo,30)

    algo,diff = diff_col(algo,long,short)

    print(algo)