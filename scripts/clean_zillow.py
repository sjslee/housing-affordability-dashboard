from pathlib import Path
import pandas as pd

RAW_FILE = Path("data/raw/zillow_zhvi_state.csv")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = PROCESSED_DIR / "zillow_zhvi_state_long.csv"

def clean_zillow():
    df = pd.read_csv(RAW_FILE)

    id_cols = [
        "RegionID",
        "SizeRank",
        "RegionName",
        "RegionType",
        "StateName"
    ]

    date_cols = [col for col in df.columns if col not in id_cols]

    df_long = df.melt(
        id_vars=id_cols,
        value_vars=date_cols,
        var_name="date",
        value_name="zhvi"
    )

    df_long["date"] = pd.to_datetime(df_long["date"], errors="coerce")
    df_long = df_long.dropna(subset=["date", "zhvi"])

    df_long = df_long.rename(columns={
        "RegionName": "state"
    })

    df_long = df_long[[
        "state",
        "date",
        "zhvi",
        "RegionID",
        "SizeRank",
        "RegionType",
        "StateName"
    ]].sort_values(["state", "date"])

    df_long.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved cleaned Zillow file to: {OUTPUT_FILE}")
    print(f"Rows: {len(df_long):,}")
    print(f"Columns: {len(df_long.columns):,}")
    print(df_long.head())

if __name__ == "__main__":
    clean_zillow()