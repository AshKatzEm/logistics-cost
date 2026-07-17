import pandas as pd
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
import time

FILES = ["ta2.xlsx", "ta3.xlsx", "td1.xlsx", "te4.xlsx"]
OUTPUT_DIR = "raw_data"

def get_session():
    session = requests.Session()
    # Retry strategy for transient network issues
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    })
    return session

def download_and_process():
    session = get_session()
    # Iterate through recent months to find the active URL
    for i in range(5):
        date = datetime.now() - timedelta(days=i*30)
        folder_slug = f"fr_trade{date.month:02d}_{date.year}"
        base_url = f"https://www.cbs.gov.il/he/publications/DocLib/{date.year}/{folder_slug}"
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        success = True
        
        # 1. Attempt download and validate file size
        for f in FILES:
            resp = session.get(f"{base_url}/{f}", timeout=20)
            # Only proceed if we get a 200 and the file looks like a real Excel file
            if resp.status_code == 200 and len(resp.content) > 1024:
                with open(os.path.join(OUTPUT_DIR, f), "wb") as file:
                    file.write(resp.content)
            else:
                success = False
                break
        
        # 2. If all files downloaded correctly, parse them
        if success:
            try:
                data = {}
                df_ta2 = pd.read_excel(f"{OUTPUT_DIR}/ta2.xlsx", header=None, engine='openpyxl')
                df_ta3 = pd.read_excel(f"{OUTPUT_DIR}/ta3.xlsx", header=None, engine='openpyxl')
                df_td1 = pd.read_excel(f"{OUTPUT_DIR}/td1.xlsx", header=None, engine='openpyxl')
                df_te4 = pd.read_excel(f"{OUTPUT_DIR}/te4.xlsx", header=None, engine='openpyxl')

                # Extraction Logic
                data['FTB_Imports_Ships_Aircraft'] = df_ta2.iloc[18, 2]
                data['FTB_Imports_Diamonds'] = df_ta2.iloc[18, 3]
                data['FTB_Imports_Fuels'] = df_ta2.iloc[18, 4]
                data['FTB_Imports_Investment_Goods'] = df_ta2.iloc[18, 5]
                data['FTB_Imports_Raw_Materials'] = df_ta2.iloc[18, 6]
                data['FTB_Imports_Consumer_Goods'] = df_ta2.iloc[18, 7]
                
                data['FTB_Exports_Wholesale_Diamonds'] = df_ta3.iloc[19, 1]
                data['FTB_Exports_Diamond_Work'] = df_ta3.iloc[19, 2]
                data['FTB_Exports_Other'] = df_ta3.iloc[19, 3]
                data['FTB_Exports_Agri_Forestry_Fishing'] = df_ta3.iloc[19, 5]
                data['FTB_Exports_Manuf_Mining_Quarry'] = df_ta3.iloc[19, 4]
                
                data['Fisher_Exp_Total'] = df_te4.iloc[16, 0]
                data['Fisher_Imp_Total'] = df_te4.iloc[16, 1]
                
                for k in range(9, 20):
                    country_name = str(df_td1.iloc[k, 1]).strip()
                    if country_name and country_name != 'nan':
                        data[f'Imp_{country_name}'] = df_td1.iloc[k, 4]
                        data[f'Exp_{country_name}'] = df_td1.iloc[k, 12]
                
                # Cleanup and Return
                for f in FILES: os.remove(os.path.join(OUTPUT_DIR, f))
                return data
            except Exception as e:
                print(f"Parsing error: {e}")
                return {}
        
    print("Could not locate valid CBS files in recent publications.")
    return {}

if __name__ == "__main__":
    result = download_and_process()
    print(result)