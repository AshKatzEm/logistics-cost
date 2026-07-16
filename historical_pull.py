import yfinance as yf
import pandas as pd

# Define tickers
tickers = ["BZ=F", "BDRY", "ZIM", "MATX", "SBLK", "FRO", "STNG"]

# 1. Download 5 years of data
df = yf.download(tickers, period="5y")['Close']

# 2. Calculate the same Weighted Basket Index
basket_cols = ["ZIM", "MATX", "SBLK", "FRO", "STNG"]
# Calculate returns, mean, and cumulative product for the index
basket_returns = df[basket_cols].pct_change().fillna(0)
df['Shipping_Basket_Index'] = 100 * (1 + basket_returns.mean(axis=1)).cumprod()

# 3. Rename columns to match your CSV headers
df = df.rename(columns={'BZ=F': 'Brent_Crude', 'BDRY': 'BDI_Proxy_BDRY'})

# 4. Save to CSV
df.reset_index(inplace=True)
df.to_csv('shipping_macro_data.csv', index=False)