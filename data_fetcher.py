import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

CSV_FILE = 'shipping_ticker_data.csv'

def fetch_exchange_rates():
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        if response.status_code == 200:
            data = response.json()
            usd_to_ils = data["rates"].get("ILS")
            usd_to_eur = data["rates"].get("EUR", 1)
            eur_to_ils = usd_to_ils / usd_to_eur
            return round(usd_to_ils, 4), round(eur_to_ils, 4)
    except Exception as e:
        print(f"Error fetching exchange rates: {e}")
    return None, None

def fetch_market_data():
    tickers = ["BZ=F", "BDRY", "ZIM", "MATX", "SBLK", "FRO", "STNG"]
    try:
        # Fetch data
        data = yf.download(tickers, period="1d", progress=False)
        # Extract last closing prices
        prices = {t: float(data['Close'][t].iloc[-1]) for t in tickers}
        
        # Robustness: If a value is NaN, replace it with None (or a fallback)
        for t in tickers:
            if pd.isna(prices[t]):
                prices[t] = None
        return prices
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return {t: None for t in tickers}

def main():
    # 1. Fetch current data
    prices = fetch_market_data()
    usd_ils, eur_ils = fetch_exchange_rates()
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 2. Validation: If core data (Brent) is missing, don't write a broken row
    if prices.get('BZ=F') is None:
        print("Data fetch failed. Skipping update to preserve integrity.")
        return 
    
    # 3. Create the row
    new_data = {
        'Date': today,
        'USD_ILS': usd_ils,
        'EUR_ILS': eur_ils,
        'Brent_Crude': prices.get('BZ=F'),
        'BDI_Proxy_BDRY': prices.get('BDRY'),
        'ZIM': prices.get('ZIM'),
        'MATX': prices.get('MATX'),
        'SBLK': prices.get('SBLK'),
        'FRO': prices.get('FRO'),
        'STNG': prices.get('STNG')
    }
    

    # 4. Read existing and Forward Fill missing values in the CSV
    df_new = pd.DataFrame([new_data])
    
    if os.path.exists(CSV_FILE) and os.stat(CSV_FILE).st_size > 0:
        # Load and fix potential bad lines
        df_existing = pd.read_csv(CSV_FILE, on_bad_lines='skip')
        
        # Forward fill existing data to ensure no gaps exist before appending
        df_existing = df_existing.ffill()
        
        # Ensure we are only concatenating non-empty dataframes
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new



    # 5. Final Save
    df_combined.to_csv(CSV_FILE, index=False)
    print(f"Updated {CSV_FILE} for {today}")

if __name__ == "__main__":
    main()