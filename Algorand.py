import yfinance as yf
from matplotlib import pyplot as plt
from pandas import DataFrame,Timestamp

def download(timeframe):
    """
    timeframe : int
        in minutes, history included in point column
    """
    algo = yf.download('algo-usd',period='5d',interval='1m')
    algo.pop('Volume')
    algo.pop('Adj Close')
    algo = algo.reset_index()

    algo = adj_tz(algo)
    algo = percent_col(algo)
    algo = point_col(algo,timeframe)
    algo = moving_avg(algo,120)
    algo = moving_avg(algo,20)

    return algo
    
def percent_col(df):
    percent = [0]
    for i,row in df.iterrows():
        if i > 0:
            new = row['Close']
            old = df.iloc[i-1]['Close']
            percent += [100*(new-old)/old]

    df['percent'] = percent
    return df

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
    return df

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

def moving_ind(df):
    ind = ['na','na']
    holding = False
    for i,row in df[2:].iterrows():
        if not holding:
            below = df.iloc[i-2]['20 avg'] < df.iloc[i-2]['120 avg']
            cross = df.iloc[i-1]['20 avg'] > df.iloc[i-1]['120 avg']
            stick = row['20 avg'] > row['120 avg']

            if below and cross and stick:
                ind += ['buy']
                holding = True
                enter = row['Close']
            else:
                ind += ['na']
        elif holding:
            slow = df.iloc[i-2]['20 avg'] < df.iloc[i-1]['20 avg']
            peak = df.iloc[i-1]['20 avg'] > row['20 avg']
            

    df['crossing ind'] = ind
    return df

if __name__ == '__main__':
    algo = download(60)

    print(moving_ind(algo)[-60:])