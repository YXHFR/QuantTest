## STEG 1 pip install ibapi matplotlib pandas mplfinance


from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import threading
import time

# --------------------------
# 1. Data Collection Class
# --------------------------
class ShortFeeDataCollector(EWrapper):
    def __init__(self):
        EWrapper.__init__(self)
        self.data = []
        
    def tickString(self, reqId, tickType, value):
        if tickType == 47:  # Shortable Share Fee
            self.data.append({
                'timestamp': pd.Timestamp.now(),
                'fee': float(value)
            })

# --------------------------
# 2. Main Collection Function
# --------------------------
def collect_short_fee_data(symbol="AAPL", duration_sec=60):
    # Create IBKR connection
    client = EClient(ShortFeeDataCollector())
    client.connect("127.0.0.1", 7497, clientId=1)
    
    # Define contract
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    
    # Start connection thread
    thread = threading.Thread(target=client.run, daemon=True)
    thread.start()
    time.sleep(1)  # Wait for connection
    
    # Request market data
    client.reqMktData(1, contract, "", False, False, [])
    
    # Collect data
    print(f"Collecting {symbol} short fee data for {duration_sec} seconds...")
    time.sleep(duration_sec)
    
    # Disconnect and format data
    client.disconnect()
    df = pd.DataFrame(client.data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# --------------------------
# 3. Advanced Visualization
# --------------------------
def visualize_short_fees(df, symbol):
    plt.figure(figsize=(14, 7))
    
    # Create main plot
    ax = plt.subplot(111)
    ax.plot(df['timestamp'], df['fee'], 
            marker='o', 
            linestyle='-', 
            color='#2c7bb6',
            markersize=8,
            linewidth=2)
    
    # Formatting
    ax.set_title(f"Real-time Short Borrow Fee: {symbol}", fontsize=16, pad=20)
    ax.set_ylabel("Fee Rate (%)", fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45, ha='right')
    
    # Annotate max/min values
    max_fee = df['fee'].max()
    min_fee = df['fee'].min()
    ax.annotate(f'Max: {max_fee:.2f}%', 
                xy=(df['timestamp'][df['fee'].idxmax()], max_fee),
                xytext=(10, 10), 
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))
    
    ax.annotate(f'Min: {min_fee:.2f}%', 
                xy=(df['timestamp'][df['fee'].idxmin()], min_fee),
                xytext=(10, -30), 
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))

    # Add statistics box
    stats_text = f"""Average: {df['fee'].mean():.2f}%
Std Dev: {df['fee'].std():.2f}%
Samples: {len(df)}"""
    ax.text(0.02, 0.98, stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', alpha=0.5))

    plt.tight_layout()
    plt.show()

# --------------------------
# 4. Execute the Program
# --------------------------
if __name__ == "__main__":
    # Collect data (60 seconds)
    fee_data = collect_short_fee_data(symbol="AAPL", duration_sec=60)
    
    # Save raw data
    fee_data.to_csv("short_fees.csv", index=False)
    
    # Visualize
    visualize_short_fees(fee_data, "AAPL")