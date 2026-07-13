import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

# Define the local file name where data will be stored
CSV_FILE = 'shipping_macro_data.csv'

def fetch_exchange_rates():
    """Fetches daily exchange rates from the free Frankfurter API."""
    try:
        # Fetching EUR and USD rates against ILS (New Israeli Shekel)
        response = requests.get("https://open.er-api.com/v6/latest/USD")
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            usd_to_ils = rates.get("ILS", None)
            
            # Get EUR to ILS via cross rate calculation
            usd_to_eur = rates.get("EUR", 1)
            eur_to_ils = usd_to_ils / usd_to_eur if usd_to_eur else None
            
            return usd_to_ils, eur_to_ils
    except Exception as e:
        print(f"Error fetching exchange rates: {e}")
    return None, None

def fetch_market_data():
    """Fetches closing prices for Brent Crude and a shipping proxy via Yahoo Finance."""
    try:
        # BZ=F is the ticker for Brent Crude Oil Futures
        # ZIM is the Haifa-based shipping giant proxy
        tickers = ["BZ=F", "ZIM"]
        data = yf.download(tickers, period="1d", progress=False)
        
        # Extract the last closing price safely
        brent_close = data['Close']['BZ=F'].iloc[-1]
        zim_close = data['Close']['ZIM'].iloc[-1]
        
        return float(brent_close), float(zim_close)
    except Exception as e:
        print(f"Error fetching market data: {e}")
    return None, None

def main():
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"Running daily fetch for {today}...")
    
    usd_ils, eur_ils = fetch_exchange_rates()
    brent_price, zim_price = fetch_market_data()
    
    # Create a dictionary for the new data row
    new_data = {
        'Date': today,
        'USD_ILS': usd_ils,
        'EUR_ILS': eur_ils,
        'Brent_Crude_USD': brent_price,
        'ZIM_Stock_USD': zim_price
    }
    
    # Convert to DataFrame
    df_new = pd.DataFrame([new_data])
    
    # Check if file exists to determine if we write headers
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        df_new.to_csv(CSV_FILE, index=False)
        print("Created new CSV file with headers.")
    else:
        # Append without writing the header again
        df_new.to_csv(CSV_FILE, mode='a', header=False, index=False)
        print("Successfully appended today's data.")

if __name__ == "__main__":
    main()