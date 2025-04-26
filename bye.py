# Market data permissions enabled in TWS
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
import matplotlib.pyplot as plt
import threading
import time
import numpy as np

class DelayedDataFetcher(EWrapper, EClient):
    def create_contract(self, symbol):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.currency = "USD"
        
        # Special handling for common ETFs
        if symbol == "SPY":
            contract.exchange = "ARCA"
            contract.primaryExchange = "ARCA"
        elif symbol in ["GLD", "IAU"]:
            contract.exchange = "ARCA"
            contract.primaryExchange = "ARCA"
        else:
            contract.exchange = "SMART"
            
        return contract
    
    def __init__(self):
        EClient.__init__(self, self)
        self.data_ready = threading.Event()
        self.price_data = {}
        self.fee_data = {}
        self.reqId_to_symbol = {}

    def tickPrice(self, reqId, tickType, price, attrib):
        print(f"tickPrice. ReqId: {reqId}, TickType: {tickType}, Price: {price}")
        if tickType == 68:  # Delayed last price
            symbol = self.reqId_to_symbol.get(reqId, None)
            if symbol:
                self.price_data[symbol] = price
                print(f"Stored price for {symbol}: {price}")

    def tickString(self, reqId, tickType, value):
        print(f"tickString. ReqId: {reqId}, TickType: {tickType}, Value: {value}")
        if tickType == 47:  # Short borrow fee (delayed)
            symbol = self.reqId_to_symbol.get(reqId, None)
            if symbol:
                self.fee_data[symbol] = float(value)
                print(f"Stored fee for {symbol}: {value}")

    def marketDataType(self, reqId, marketDataType):
        """Callback to confirm the market data type."""
        print(f"MarketDataType. ReqId: {reqId}, Type: {marketDataType}")

    def get_delayed_data(self, symbols):
        self.__init__()  # Reset state
        self.connect("127.0.0.1", 7497, clientId=1)
        
        # Start connection thread
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        time.sleep(2)  # Longer connection wait

        # Request delayed market data
        self.reqMarketDataType(3)  # 3 = Delayed data

        results = []
        for reqId, symbol in enumerate(symbols, 1):
            contract = self.create_contract(symbol)
            self.reqId_to_symbol[reqId] = symbol

            # Request market data
            self.reqMktData(reqId, contract, "", False, False, [])
            time.sleep(1)  # Required delay between requests

        # Wait for data to arrive
        time.sleep(50)

        # Compile results
        for symbol in symbols:
            price = self.price_data.get(symbol, np.nan)
            fee = self.fee_data.get(symbol, np.nan)
            
            # Convert to numeric types
            try:
                price = float(price)
            except:
                price = np.nan
                
            results.append({
                "Symbol": symbol,
                "Price": price,
                "Short Fee (%)": fee
            })

        self.disconnect() 
        df = pd.DataFrame(results)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        return df.dropna()

    

def plot_data(df):
    if df.empty:
        print("No data received - check market hours (9:30 AM - 4:00 PM ET)")
        return
    
    plt.figure(figsize=(12, 6))
    
    # Price plot
    plt.subplot(2, 1, 1)
    plt.bar(df['Symbol'], df['Price'], color=['blue', 'gold', 'green'])
    plt.title('Delayed Market Data (15-min delay)')
    plt.ylabel('Price (USD)')
    
    # Fee plot
    plt.subplot(2, 1, 2)
    plt.bar(df['Symbol'], df['Short Fee (%)'], color=['blue', 'gold', 'green'])
    plt.ylabel('Short Fee (%)')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Example usage
    fetcher = DelayedDataFetcher()
    
    # Try IBKR connection first
    print("Attempting to fetch delayed data from IBKR...")
    live_df = fetcher.get_delayed_data(["SPY", "GLD", "IAU"])
    
    print(live_df)
    plot_data(live_df)