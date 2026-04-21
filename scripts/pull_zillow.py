from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

ZILLOW_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zhvi/"
    "State_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)

def pull_zillow() -> Path:
    df = pd.read_csv(ZILLOW_URL)

    output_path = RAW_DIR / "zillow_zhvi_state.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved Zillow data to: {output_path}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns):,}")

    return output_path

if __name__ == "__main__":
    pull_zillow()
