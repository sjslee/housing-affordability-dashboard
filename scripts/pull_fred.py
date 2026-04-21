from pathlib import Path
import pandas as pd
from fredapi import Fred

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RAW_DIR / "fred_macro_data.csv"

# Replace this with your own FRED API key for now
FRED_API_KEY = "985a633fe44b80d533a07be11c51ccb2"

SERIES = {
    "mortgage_rate": "MORTGAGE30US",   # 30-Year Fixed Rate Mortgage Average
    "cpi": "CPIAUCSL",                 # CPI All Urban Consumers
    "unemployment_rate": "UNRATE",     # Unemployment Rate
    "median_household_income": "MEHOINUSA672N"  # Median Household Income in the US
}

def pull_fred():
    fred = Fred(api_key=FRED_API_KEY)

    dfs = []

    for name, series_id in SERIES.items():
        s = fred.get_series(series_id)
        df = s.reset_index()
        df.columns = ["date", name]
        dfs.append(df)

    df_final = dfs[0]
    for df in dfs[1:]:
        df_final = df_final.merge(df, on="date", how="outer")

    df_final = df_final.sort_values("date")
    df_final.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved FRED data to: {OUTPUT_FILE}")
    print(f"Rows: {len(df_final):,}")
    print(f"Columns: {len(df_final.columns):,}")
    print(df_final.tail())

if __name__ == "__main__":
    pull_fred()