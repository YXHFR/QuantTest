import backtrader as bt
import datetime
import yfinance as yf
import matplotlib.pyplot as plt

# Download data
cerebro = bt.Cerebro()
df = yf.download('AAPL', start='2020-01-01')

df = df[['Open', 'High', 'Low', 'Close', 'Volume']]  # Select required columns
df.columns = ['open', 'high', 'low', 'close', 'volume']  # Rename columns to lowercase
df.index.name = 'datetime'  # Set index name to 'datetime'

feed = bt.feeds.PandasData(dataname=df)
cerebro.adddata(feed)
cerebro.run()
cerebro.plot()