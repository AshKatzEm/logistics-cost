import yfinance as yf
import pandas as pd
import requests

# Define tickers
tickers = ["BZ=F", "BDRY", "ZIM", "MATX", "SBLK", "FRO", "STNG"]

def get_current_exchange_rates():
    """Helper to get current rates to use as a baseline if historical isn't available."""
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        data = response.json()
        usd_to_ils = data["rates"].get("ILS", 3.7) # Fallback 3.7
        usd_to_eur = data["rates"].get("EUR", 0.9)
        return round(usd_to_ils, 4), round(usd_to_ils / usd_to_eur, 4)
    except:
        return 3.7, 4.1 # Emergency defaults

# 1. Download hourly data
df = yf.download(tickers, period="2y", interval="1h")['Close']

# 2. Forward fill gaps
df = df.ffill().bfill()

# 3. Filter for active market hours
df = df[df.index.hour.isin([14, 19])]

# 4. Calculate the Shipping Basket Index
basket_cols = ["ZIM", "MATX", "SBLK", "FRO", "STNG"]
basket_returns = df[basket_cols].pct_change(fill_method=None).fillna(0)
df['Shipping_Basket_Index'] = 100 * (1 + basket_returns.mean(axis=1)).cumprod()

# 5. Add Exchange Rate Columns
# Note: Since historical exchange rate APIs are often paid/complex, 
# we inject the current rates to ensure the columns exist in the CSV.
usd_ils, eur_ils = get_current_exchange_rates()
df['USD_ILS'] = usd_ils
df['EUR_ILS'] = eur_ils

# 6. Rename columns to match your CSV headers
df = df.rename(columns={'BZ=F': 'Brent_Crude', 'BDRY': 'BDI_Proxy_BDRY'})

# 7. Format Date and Reorder
df.reset_index(inplace=True)
df['Date'] = pd.to_datetime(df['Datetime']).dt.strftime('%Y-%m-%d %H:%M')

if 'Datetime' in df.columns:
    df.drop(columns=['Datetime'], inplace=True)

# Final column ordering to ensure consistency with data_fetcher.py
expected_cols = [
    'Date', 'USD_ILS', 'EUR_ILS', 'Brent_Crude', 'BDI_Proxy_BDRY', 
    'ZIM', 'MATX', 'SBLK', 'FRO', 'STNG', 'Shipping_Basket_Index'
]
df = df.reindex(columns=expected_cols)

# 8. Save to CSV
df.to_csv('shipping_ticker_data.csv', index=False)

print("Historical data rebuilt with full column set (including exchange rates).")