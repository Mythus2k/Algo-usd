import yfinance as yf

algo = yf.download('algo-usd',period='5d',interval='1m')
algo = algo.reset_index()

percent = [0]
for i,row in algo.iterrows():
    if i > 0:
        new = row['Close']
        old = algo.iloc[i-1]['Close']
        change = 100*(new-old)/old
        percent += [change]

algo['percent'] = percent

print(algo)