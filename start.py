from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
import backtrader as bt
import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt



class EMACrossoverStrategy(bt.Strategy):
    params = (
        ('short_ema', 10),  # Short-term EMA period
        ('long_ema', 30),   # Long-term EMA period
    )

    def __init__(self):
        # Define the short-term and long-term EMAs
        self.ema_short = bt.indicators.EMA(self.data.close, period=self.params.short_ema)
        self.ema_long = bt.indicators.EMA(self.data.close, period=self.params.long_ema)

        # To keep track of pending orders
        self.order = None

    def log(self, txt, dt=None):
        ''' Logging function for this strategy '''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return  # Order submitted/accepted, no action needed

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None  # Reset the order

    def next(self):
        # Log the closing price
        self.log(f'Close, {self.data.close[0]:.2f}')

        # Check if an order is pending
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # Buy if short EMA crosses above long EMA
            if self.ema_short[0] > self.ema_long[0] and self.ema_short[-1] <= self.ema_long[-1]:
                self.log(f'BUY CREATE, {self.data.close[0]:.2f}')
                self.order = self.buy()
        else:
            # Sell if short EMA crosses below long EMA
            if self.ema_short[0] < self.ema_long[0] and self.ema_short[-1] >= self.ema_long[-1]:
                self.log(f'SELL CREATE, {self.data.close[0]:.2f}')
                self.order = self.sell()


if __name__ == '__main__':
    # Create a cerebro instance
    cerebro = bt.Cerebro()

    # Add the strategy
    cerebro.addstrategy(EMACrossoverStrategy)

# Load data from Yahoo Finance
# Download data using yfinance
df = yf.download('MSTR', start='2023-10-01', end='2023-12-31', interval='1h')

# Preprocess the DataFrame to match Backtrader's expected format
df = df[['Open', 'High', 'Low', 'Close', 'Volume']]  # Select required columns
df.columns = ['open', 'high', 'low', 'close', 'volume']  # Rename columns to lowercase
df.index.name = 'datetime'  # Set index name to 'datetime'

# Convert to Backtrader feed
data = bt.feeds.PandasData(dataname=df)

# Add the data to Cerebro
cerebro.adddata(data)

# Set the starting cash
cerebro.broker.setcash(100000.0)

# Set the commission (0.1%)
cerebro.broker.setcommission(commission=0.001)

# Print the starting portfolio value
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Run the strategy
cerebro.run()

# Print the final portfolio value
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Plot the results
cerebro.plot(style='candlestick')