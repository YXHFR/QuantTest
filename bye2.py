"""
IBKR Delayed Market Data Fetcher (Enhanced)
Fetches latest available delayed data without subscriptions
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
import matplotlib.pyplot as plt
import threading
import time
import numpy as np
from datetime import datetime, time as dt_time

class EnhancedDelayedFetcher(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data_lock = threading.Lock()
        self.price_data = {}
        self.fee_data = {}
        self.reqId_to_symbol = {}
        self.connected = False
        self.error_log = []

    def error(self, reqId, errorCode, errorString):
        if errorCode not in [2104, 2106, 2158]:  # Filter connection messages
            self.error_log.append(f"Req {reqId}: {errorCode} - {errorString}")

    def connectAck(self):
        self.connected = True

    def connectionClosed(self):
        self.connected = False

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4:  # Last price
            with self.data_lock:
                self.price_data[self.reqId_to_symbol[reqId]] = price

    def tickString(self, reqId, tickType, value):
        if tickType == 47:  # Short borrow fee
            with self.data_lock:
                try:
                    self.fee_data[self.reqId_to_symbol[reqId]] = float(value)
                except:
                    pass

    def get_market_data(self, symbols):
        if not self._check_market_hours():
            print("Market is closed - delayed data unavailable")
            return pd.DataFrame()

        self._reset()
        self.connect("127.0.0.1", 7497, clientId=1)
        
        # Start connection thread
        api_thread = threading.Thread(target=self.run, daemon=True)
        api_thread.start()
        
        # Wait for connection
        for _ in range(10):
            if self.connected:
                break
            time.sleep(0.5)
        
        if not self.connected:
            print("Failed to connect to TWS")
            return pd.DataFrame()

        # Request market data
        req_id = 1
        for symbol in symbols:
            contract = self._create_contract(symbol)
            self.reqId_to_symbol[req_id] = symbol
            self.reqMktData(req_id, contract, "233", False, False, [])
            req_id += 1
            time.sleep(0.5)  # IBKR rate limit

        # Wait for data with timeout
        start_time = time.time()
        while (time.time() - start_time) < 15:  # 15-second timeout
            if len(self.price_data) >= len(symbols):
                break
            time.sleep(1)

        self.disconnect()

        # Compile results
        results = []
        for symbol in symbols:
            results.append({
                "Symbol": symbol,
                "Price": self.price_data.get(symbol, np.nan),
                "Short Fee (%)": self.fee_data.get(symbol, np.nan),
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        df = pd.DataFrame(results)
        numeric_cols = ["Price", "Short Fee (%)"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        return df.dropna(subset=numeric_cols, how='all')

    def _create_contract(self, symbol):
        contract = Contract()
        contract.symbol = symbol.upper()
        contract.secType = "STK"
        contract.currency = "USD"
        
        # Optimized exchange mapping
        etf_exchanges = {
            "SPY": "ARCA",
            "GLD": "ARCA",
            "IAU": "ARCA",
            "QQQ": "NASDAQ",
            "IWM": "ARCA"
        }
        
        contract.exchange = etf_exchanges.get(symbol, "SMART")
        contract.primaryExchange = etf_exchanges.get(symbol, "ISLAND")
        return contract

    def _check_market_hours(self):
        now = datetime.now().astimezone()
        market_open = dt_time(9, 30)
        market_close = dt_time(16, 0)
        return (now.weekday() < 5 and  # Mon-Fri
                market_open <= now.time() <= market_close)

    def _reset(self):
        with self.data_lock:
            self.price_data.clear()
            self.fee_data.clear()
            self.reqId_to_symbol.clear()
        self.error_log.clear()

def visualize_results(df):
    if df.empty:
        print("No valid data to display")
        return

    plt.figure(figsize=(14, 8))
    
    # Price plot
    plt.subplot(2, 1, 1)
    plt.bar(df['Symbol'], df['Price'], color='steelblue')
    plt.title(f"Delayed Market Data - {df['Timestamp'].iloc[0]}")
    plt.ylabel('Price (USD)')
    
    # Fee plot
    plt.subplot(2, 1, 2)
    plt.bar(df['Symbol'], df['Short Fee (%)'], color='firebrick')
    plt.ylabel('Short Fee (%)')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    fetcher = EnhancedDelayedFetcher()
    symbols = ["SPY", "GLD", "IAU", "QQQ"]  # Example symbols
    
    print("Fetching latest delayed data...")
    data_df = fetcher.get_market_data(symbols)
    
    if not data_df.empty:
        print("\nLatest Available Data:")
        print(data_df[["Symbol", "Price", "Short Fee (%)", "Timestamp"]])
        visualize_results(data_df)
    else:
        print("\nFailed to retrieve data. Check:")
        print("- TWS is running and connected")
        print("- Market hours (9:30 AM - 4:00 PM ET)")
        print("- Symbol validity (try SPY, AAPL, MSFT)")
        if fetcher.error_log:
            print("\nError messages:")
            print("\n".join(fetcher.error_log))