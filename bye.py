"""
IBKR Delayed Market Data Fetcher using ib_insync
This approach is often more reliable than using ibapi directly

Prerequisites:
- TWS Running on port 7497 (paper trading)
- ib_insync installed (pip install ib_insync)
- Market data permissions enabled in TWS
"""

from ib_insync import *
import pandas as pd
import matplotlib.pyplot as plt
import time
import numpy as np

def fetch_delayed_data(symbols):
    """Fetch delayed market data using ib_insync"""
    print("Starting connection attempt...")
    
    try:
        # Create IB instance
        ib = IB()
        
        # Try multiple client IDs
        for client_id in [10, 20, 30, 40, 50]:
            try:
                print(f"Trying to connect with client ID {client_id}...")
                ib.connect('127.0.0.1', 7497, clientId=client_id, readonly=True, timeout=5)
                if ib.isConnected():
                    print(f"✅ Connected successfully with client ID {client_id}")
                    break
            except Exception as e:
                print(f"Failed with client ID {client_id}: {str(e)}")
                continue
        
        if not ib.isConnected():
            print("❌ Could not connect with any client ID")
            return pd.DataFrame()
            
        # Get market data for symbols
        results = []
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
                    "Short Fee (%)": short_fee
                })
                print(f"Received price for {symbol}: {price}")
            except Exception as e:
                print(f"Error fetching data for {symbol}: {str(e)}")
                results.append({
                    "Symbol": symbol,
                    "Price": np.nan,
                    "Short Fee (%)": np.nan
                })
            
            # Small delay between requests
            ib.sleep(1)
    
    except Exception as e:
        print(f"Error during connection: {str(e)}")
        return pd.DataFrame()
    finally:
        # Disconnect when done
        if 'ib' in locals() and ib.isConnected():
            print("Disconnecting...")
            ib.disconnect()
    
    return pd.DataFrame(results)

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