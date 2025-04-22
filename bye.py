from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
import threading
import time

class AssetDataFetcher(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []
        self.price_data = {}
        self.fee_data = {}
        
    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4:  # Last price
            symbol = self.reqId_to_symbol[reqId]
            self.price_data[symbol] = price
            
    def tickString(self, reqId, tickType, value):
        if tickType == 47:  # Short borrow fee
            symbol = self.reqId_to_symbol[reqId]
            self.fee_data[symbol] = float(value)
    
    def get_asset_data(self, symbols):
        self.reqId_to_symbol = {}
        self.connect("127.0.0.1", 7497, clientId=1)
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        time.sleep(1)  # Wait for connection
        
        # Request market data for each symbol
        for reqId, symbol in enumerate(symbols, 1):
            self.reqId_to_symbol[reqId] = symbol
            contract = self._create_contract(symbol)
            self.reqMktData(reqId, contract, "", False, False, [])
        
        # Wait 5 seconds to collect data
        print("Fetching live data...")
        time.sleep(5)
        
        # Compile results
        results = []
        for symbol in symbols:
            results.append({
                "Symbol": symbol,
                "Price": self.price_data.get(symbol, "N/A"),
                "Short Fee (%)": self.fee_data.get(symbol, "N/A")
            })
        
        self.disconnect()
        return pd.DataFrame(results)
    
    def _create_contract(self, symbol):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"  # For ETFs
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

# Usage
fetcher = AssetDataFetcher()
assets = ["SPY", "GLD", "IAU"]  # SPDR S&P 500 & Gold ETFs
df = fetcher.get_asset_data(assets)
print(df)