from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
import threading
import time
import matplotlib.pyplot as plt

class DelayedDataFetcher(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []
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
        self.reqId_to_symbol = {}
        self.connect("127.0.0.1", 7497, clientId=1)
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        time.sleep(2)  # Longer connection wait

        # Request delayed market data
        self.reqMarketDataType(3)  # 3 = Delayed data

        results = []
        for reqId, symbol in enumerate(symbols, 1):
            contract = self._create_contract(symbol)
            self.reqId_to_symbol[reqId] = symbol

            # Request market data
            self.reqMktData(reqId, contract, "", False, False, [])
            time.sleep(1)  # Required delay between requests

        # Wait for data to arrive
        time.sleep(5)

        # Compile results
        for symbol in symbols:
            results.append({
                "Symbol": symbol,
                "Price": self.price_data.get(symbol, "N/A"),
                "Short Fee (%)": self.fee_data.get(symbol, "N/A"),
                "Data Type": "Delayed (15 min)"
            })

        self.disconnect()
        return pd.DataFrame(results)
    
    def _create_contract(self, symbol):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        
        # Special settings for popular ETFs
        if symbol in ["GLD", "IAU"]:
            contract.primaryExchange = "ARCA"
        elif symbol == "SPY":
            contract.primaryExchange = "NYSE"
            
        return contract

# Usage
fetcher = DelayedDataFetcher()
assets = ["SPY", "GLD", "IAU"]  # Try these popular ETFs
df = fetcher.get_delayed_data(assets)

print("\nDelayed Market Data (15-min delay):")
print(df)

# Simple Visualization
if not df.empty:
    df[["Symbol", "Price", "Short Fee (%)"]].plot(
        kind='bar', 
        x='Symbol',
        subplots=True,
        layout=(2,1),
        figsize=(10,8),
        title="Delayed Market Data"
    )
    plt.tight_layout()
    plt.show()