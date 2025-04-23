# Market data permissions enabled in TWS


from unittest import result
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
import matplotlib.pyplot as plt
import time
import numpy as np

class DelayedDataFetcher(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data_ready = threading.Event()
        self.price_data = {}
        self.fee_data = {}
        self.reqId_to_symbol = {}

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4:  # Last price (delayed)
            symbol = self.reqId_to_symbol[reqId]
            self.price_data[symbol] = price

    def tickString(self, reqId, tickType, value):
        if tickType == 47:  # Short borrow fee (delayed)
            symbol = self.reqId_to_symbol[reqId]
            self.fee_data[symbol] = float(value)

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
        time.sleep(5)

        # Compile results
        for symbol in symbols:
            print(f"Requesting data for {symbol}...")
            
            # Create contract
            if symbol in ["SPY", "GLD", "IAU"]:
                contract = Stock(symbol, 'ARCA', 'USD')
            else:
                contract = Stock(symbol, 'SMART', 'USD')
                
            # Request market data (with 2-second timeout)
            try:
                # Non-snapshot delayed data
                ib.reqMarketDataType(3)  # 3 = Delayed
                ib.qualifyContracts(contract)
                
                ticker = ib.reqMktData(contract)
                
                # Wait for data to arrive
                timeout = time.time() + 5
                while not ticker.last and time.time() < timeout:
                    ib.sleep(0.1)
                
                price = ticker.last if ticker.last else np.nan
                
                # Try to get short fee (not always available)
                short_fee = np.nan
                try:
                    ib.sleep(0.5)  # give time for other data to arrive
                    if hasattr(ticker, 'shortableShares'):
                        short_fee = ticker.shortableShares
                except:
                    pass
                
            results.append({
                "Symbol": symbol,
                "Price": price,
                "Short Fee (%)": fee
            })

        self.disconnect() 
        df = pd.DataFrame(results)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        return df.dropna()

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

def plot_data(df):
    if df.empty or df['Price'].isna().all():
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
    print("Attempting to fetch delayed data from IBKR using ib_insync...")
    symbols = ["SPY", "GLD", "IAU"]
    
    live_df = fetch_delayed_data(symbols)
    
    if not live_df.empty and not live_df['Price'].isna().all():
        print("Successfully fetched delayed data:")
        print(live_df)
        plot_data(live_df)
    else:
        # Fallback to sample data
        print("\nUsing sample data instead...")
        sample_data = {
            "Symbol": ["SPY", "GLD", "IAU"],
            "Price": [445.21, 180.55, 35.12],
            "Short Fee (%)": [0.3, 0.45, 0.5]
        }
        sample_df = pd.DataFrame(sample_data)
        plot_data(sample_df)
        
        print("\n=== Additional Troubleshooting Steps ===")
        print("1. Is your IBKR account funded? Some demo accounts require funding")
        print("2. Do you have market data subscriptions for these symbols?")
        print("3. Is it currently market hours? (9:30 AM - 4:00 PM ET, Mon-Fri)")
        print("4. Try completely restarting your computer and TWS")
        print("5. Check if your TWS version matches your API version")