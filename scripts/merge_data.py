from pathlib import Path
import pandas as pd

ZILLOW_FILE = Path("data/processed/zillow_zhvi_state_long.csv")
FRED_FILE = Path("data/processed/fred_macro_monthly.csv")

PROCESSED_DIR = Path("data/processed")
OUTPUT_FILE = PROCESSED_DIR / "housing_dataset.csv"

def merge_data():
    df_zillow = pd.read_csv(ZILLOW_FILE)
    df_fred = pd.read_csv(FRED_FILE)

    # Convert date columns
    df_zillow["date"] = pd.to_datetime(df_zillow["date"])
    df_fred["date"] = pd.to_datetime(df_fred["date"])

    # Merge on date
    df = df_zillow.merge(df_fred, on="date", how="left")

    # Drop rows where key values are missing
    df = df.dropna(subset=["zhvi", "mortgage_rate"])

    # Sort for time series
    df = df.sort_values(["state", "date"])

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved merged dataset to: {OUTPUT_FILE}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns):,}")
    print(df.head())

if __name__ == "__main__":
    merge_data()