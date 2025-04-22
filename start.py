from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
import time 
import threading
import matplotlib.pyplot as plt

class IBWrapper(EWrapper):
    def __init__(self):
        self.data = []
        
    def tickString(self, reqId, tickType, value):
        if tickType == 47:  # Shortable Share Fee
            self.data.append({
                'timestamp': pd.Timestamp.now(),
                'fee': float(value)
            })

class IBClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

def fetch_short_fee(symbol="AAPL", sec_type="STK", exchange="SMART", currency="USD"):
    # Create contract
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = currency
    
    # Connect to TWS
    wrapper = IBWrapper()
    client = IBClient(wrapper)
    client.connect("127.0.0.1", 7497, clientId=1)
    
    # Start a daemon thread to handle messages
    thread = threading.Thread(target=client.run, daemon=True)
    thread.start()
    time.sleep(1)  # Wait for connection
    
    # Request market data
    client.reqMktData(1, contract, "", False, False, [])
    
    # Collect data for 60 seconds
    print("Collecting data for 60 seconds...")
    time.sleep(60)
    
    # Disconnect
    client.disconnect()
    return pd.DataFrame(wrapper.data)

# Fetch data
df = fetch_short_fee()