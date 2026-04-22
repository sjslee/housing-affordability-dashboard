from pathlib import Path
import pandas as pd
import numpy as np
import json

HIST_FILE = Path("data/processed/housing_with_affordability.csv")
FORECAST_FILE = Path("data/processed/state_forecasts.csv")
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


def label_affordability(x):
    if x is None or pd.isna(x):
        return "Unknown"
    elif x >= 5:
        return "High Affordability"
    elif x >= 3:
        return "Moderate Affordability"
    else:
        return "Low Affordability"


def clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    return obj


def export_dashboard():
    hist = pd.read_csv(HIST_FILE)
    fc = pd.read_csv(FORECAST_FILE)

    hist["date"] = pd.to_datetime(hist["date"])
    fc["date"] = pd.to_datetime(fc["date"])

    hist = hist.sort_values(["state", "date"]).copy()
    fc = fc.sort_values(["state", "date"]).copy()

    latest_hist_date = hist["date"].max()

    # Latest historical row per state
    current = hist[hist["date"] == latest_hist_date].copy()

    # Final forecast row per state (12-month-ahead point)
    final_fc = (
        fc.sort_values(["state", "date"])
          .groupby("state", as_index=False)
          .tail(1)
          .copy()
    )

    # Merge latest actual + final forecast
    summary = current.merge(
        final_fc[["state", "forecast_home_price", "forecast_affordability_ratio"]],
        on="state",
        how="left"
    )

    # Replace inf with NaN, then drop bad rows
    summary = summary.replace([np.inf, -np.inf], np.nan)
    summary = summary.dropna(subset=[
        "zhvi",
        "affordability_ratio",
        "forecast_home_price",
        "forecast_affordability_ratio",
        "mortgage_rate"
    ])

    summary["change"] = (
        summary["forecast_affordability_ratio"] - summary["affordability_ratio"]
    )
    summary["label"] = summary["affordability_ratio"].apply(label_affordability)
    summary["state_code"] = summary["state"].map(STATE_ABBREV)

    # KPIs
    kpis = {
        "current_home_price": float(summary["zhvi"].mean()),
        "current_affordability_ratio": float(summary["affordability_ratio"].mean()),
        "forecast_change": float(summary["change"].mean()),
        "mortgage_rate": float(summary["mortgage_rate"].mean())
    }

    # Map data
    map_data = []
    for _, row in summary.iterrows():
        if pd.isna(row["state_code"]):
            continue

        map_data.append({
            "state": row["state"],
            "state_code": row["state_code"],
            "current_affordability_ratio": float(row["affordability_ratio"]),
            "forecast_affordability_ratio": float(row["forecast_affordability_ratio"]),
            "affordability_change": float(row["change"])
        })

    # Table data
    table_data = []
    for _, row in summary.iterrows():
        table_data.append({
            "state": row["state"],
            "current_price": float(row["zhvi"]),
            "forecast_price": float(row["forecast_home_price"]),
            "current_ratio": float(row["affordability_ratio"]),
            "forecast_ratio": float(row["forecast_affordability_ratio"]),
            "change": float(row["change"]),
            "label": row["label"]
        })

    # State history + forecast series
    state_series = []
    for state, g_hist in hist.groupby("state"):
        g_hist = g_hist.sort_values("date").copy()
        g_fc = fc[fc["state"] == state].sort_values("date").copy()

        g_hist = g_hist.replace([np.inf, -np.inf], np.nan)
        g_fc = g_fc.replace([np.inf, -np.inf], np.nan)

        g_hist = g_hist.dropna(subset=["zhvi", "affordability_ratio"])
        g_fc = g_fc.dropna(subset=["forecast_home_price", "forecast_affordability_ratio"])

        history = [
            {
                "date": d.strftime("%Y-%m-%d"),
                "home_price": float(p),
                "affordability_ratio": float(a)
            }
            for d, p, a in zip(
                g_hist["date"],
                g_hist["zhvi"],
                g_hist["affordability_ratio"]
            )
        ]

        forecast = [
            {
                "date": d.strftime("%Y-%m-%d"),
                "home_price": float(p),
                "affordability_ratio": float(a)
            }
            for d, p, a in zip(
                g_fc["date"],
                g_fc["forecast_home_price"],
                g_fc["forecast_affordability_ratio"]
            )
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

    # Clean JSON-safe values
    dashboard_data = clean_for_json(dashboard_data)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2, allow_nan=False)

    print(f"Saved dashboard JSON to: {OUTPUT_FILE}")


if __name__ == "__main__":
    export_dashboard()
