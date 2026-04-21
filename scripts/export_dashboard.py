from pathlib import Path
import pandas as pd
import json

INPUT_FILE = Path("data/processed/housing_with_affordability.csv")
OUTPUT_FILE = Path("dashboard/housing-dashboard-data.json")

STATE_ABBREV = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

def label_affordability(ratio):
    if ratio >= 2.0:
        return "Affordable"
    elif ratio >= 1.4:
        return "Moderate"
    else:
        return "Stretched"

def export_dashboard():
    df = pd.read_csv(INPUT_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["state", "date"]).copy()

    latest_date = df["date"].max()

    # current snapshot
    current = df[df["date"] == latest_date].copy()

    # simple placeholder forecast:
    # use last observed values as forecast values for now
    current["forecast_price"] = current["zhvi"]
    current["forecast_ratio"] = current["affordability_ratio"]
    current["change"] = current["forecast_ratio"] - current["affordability_ratio"]
    current["label"] = current["affordability_ratio"].apply(label_affordability)
    current["state_code"] = current["state"].map(STATE_ABBREV)

    # KPIs: national averages
    kpis = {
        "current_home_price": float(current["zhvi"].mean()),
        "current_affordability_ratio": float(current["affordability_ratio"].mean()),
        "forecast_change": float(current["change"].mean()),
        "mortgage_rate": float(current["mortgage_rate"].mean())
    }

    # Map data
    map_data = []
    for _, row in current.iterrows():
        if pd.isna(row["state_code"]):
            continue
        map_data.append({
            "state": row["state"],
            "state_code": row["state_code"],
            "current_affordability_ratio": float(row["affordability_ratio"]),
            "forecast_affordability_ratio": float(row["forecast_ratio"]),
            "affordability_change": float(row["change"])
        })

    # Table data
    table_data = []
    for _, row in current.iterrows():
        table_data.append({
            "state": row["state"],
            "current_price": float(row["zhvi"]),
            "forecast_price": float(row["forecast_price"]),
            "current_ratio": float(row["affordability_ratio"]),
            "forecast_ratio": float(row["forecast_ratio"]),
            "change": float(row["change"]),
            "label": row["label"]
        })

    # State series for charts
    state_series = []
    for state, g in df.groupby("state"):
        g = g.sort_values("date").copy()

        history = [
            {
                "date": d.strftime("%Y-%m-%d"),
                "home_price": float(p),
                "affordability_ratio": float(a)
            }
            for d, p, a in zip(g["date"], g["zhvi"], g["affordability_ratio"])
        ]

        # placeholder forecast: repeat last point 12 times monthly
        last_row = g.iloc[-1]
        forecast_dates = pd.date_range(
            last_row["date"] + pd.offsets.MonthEnd(1),
            periods=12,
            freq="ME"
        )

        forecast = [
            {
                "date": d.strftime("%Y-%m-%d"),
                "home_price": float(last_row["zhvi"]),
                "affordability_ratio": float(last_row["affordability_ratio"])
            }
            for d in forecast_dates
        ]

        state_series.append({
            "state": state,
            "history": history,
            "forecast": forecast
        })

    dashboard_data = {
        "default_state": "Wisconsin",
        "kpis": kpis,
        "map_data": map_data,
        "table_data": table_data,
        "state_series": state_series
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2)

    print(f"Saved dashboard JSON to: {OUTPUT_FILE}")

if __name__ == "__main__":
    export_dashboard()