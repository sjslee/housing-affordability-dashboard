from pathlib import Path
import pandas as pd

RAW_FILE = Path("data/raw/fred_macro_data.csv")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = PROCESSED_DIR / "fred_macro_monthly.csv"

def clean_fred():
    df = pd.read_csv(RAW_FILE)
    df["date"] = pd.to_datetime(df["date"])

    # Set date as index for resampling
    df = df.set_index("date").sort_index()

    # Resample to month-end
    df_monthly = df.resample("ME").mean()

    # Forward fill slower-moving series where appropriate
    df_monthly["cpi"] = df_monthly["cpi"].ffill()
    df_monthly["unemployment_rate"] = df_monthly["unemployment_rate"].ffill()
    df_monthly["median_household_income"] = df_monthly["median_household_income"].ffill()

    df_monthly = df_monthly.reset_index()

    df_monthly.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved cleaned FRED file to: {OUTPUT_FILE}")
    print(f"Rows: {len(df_monthly):,}")
    print(f"Columns: {len(df_monthly.columns):,}")
    print(df_monthly.tail())

if __name__ == "__main__":
    clean_fred()