import os
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import argparse

# Define the local file name
CSV_FILE = 'shipping_macro_data.csv'

def fetch_exchange_rates():
    """Fetches daily USD/ILS and EUR/ILS rates."""
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
    """Fetches market prices via yfinance."""
    # BZ=F: Brent, BDRY: Dry Bulk, others: Shipping stocks
    tickers = ["BZ=F", "BDRY", "ZIM", "MATX", "SBLK", "FRO", "STNG"]
    try:
        data = yf.download(tickers, period="1d", progress=False)
        # Safely extract last closing prices
        prices = {t: float(data['Close'][t].iloc[-1]) for t in tickers}
        return prices
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return {t: None for t in tickers}

def main():
    # 1. Fetch current data
    prices = fetch_market_data()
    usd_ils, eur_ils = fetch_exchange_rates()
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 2. Build row
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
    
    # 3. Append to CSV
    df_new = pd.DataFrame([new_data])
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        df_new.to_csv(CSV_FILE, index=False)
    else:
        df_existing = pd.read_csv(CSV_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_csv(CSV_FILE, index=False)
    
    print(f"Updated {CSV_FILE} for {today}")

if __name__ == "__main__":
    main()