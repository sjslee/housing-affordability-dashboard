from pathlib import Path
import warnings
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")

INPUT_FILE = Path("data/processed/housing_with_affordability.csv")
OUTPUT_FILE = Path("data/processed/state_forecasts.csv")

FORECAST_HORIZON = 12
ARIMA_ORDER = (2, 1, 1)

TAX_RATES = {
    "Alabama": 0.0041, "Alaska": 0.0119, "Arizona": 0.0063, "Arkansas": 0.0061,
    "California": 0.0071, "Colorado": 0.0049, "Connecticut": 0.0180, "Delaware": 0.0056,
    "Florida": 0.0083, "Georgia": 0.0092, "Hawaii": 0.0032, "Idaho": 0.0063,
    "Illinois": 0.0195, "Indiana": 0.0081, "Iowa": 0.0150, "Kansas": 0.0141,
    "Kentucky": 0.0083, "Louisiana": 0.0056, "Maine": 0.0124, "Maryland": 0.0111,
    "Massachusetts": 0.0123, "Michigan": 0.0132, "Minnesota": 0.0105, "Mississippi": 0.0081,
    "Missouri": 0.0097, "Montana": 0.0083, "Nebraska": 0.0173, "Nevada": 0.0050,
    "New Hampshire": 0.0186, "New Jersey": 0.0223, "New Mexico": 0.0072, "New York": 0.0140,
    "North Carolina": 0.0078, "North Dakota": 0.0098, "Ohio": 0.0136, "Oklahoma": 0.0087,
    "Oregon": 0.0090, "Pennsylvania": 0.0135, "Rhode Island": 0.0137, "South Carolina": 0.0057,
    "South Dakota": 0.0114, "Tennessee": 0.0061, "Texas": 0.0160, "Utah": 0.0056,
    "Vermont": 0.0176, "Virginia": 0.0080, "Washington": 0.0084, "West Virginia": 0.0058,
    "Wisconsin": 0.0161, "Wyoming": 0.0055, "District of Columbia": 0.0056
}

INSURANCE_RATE = 0.005


def monthly_payment(principal, annual_rate, n_months=360):
    """
    Standard mortgage payment formula.
    principal: loan amount
    annual_rate: annual mortgage rate in percent
    """
    r = annual_rate / 100 / 12

    if pd.isna(principal) or pd.isna(annual_rate):
        return np.nan

    if r == 0:
        return principal / n_months

    return principal * (r * (1 + r) ** n_months) / ((1 + r) ** n_months - 1)


def forecast_one_state(state_df, horizon=12, order=(1, 1, 1)):
    state_df = state_df.sort_values("date").copy()

    state_name = state_df["state"].iloc[0]
    last_date = pd.to_datetime(state_df["date"].iloc[-1])

    y = state_df["zhvi"].astype(float)

    if len(y) < 24:
        raise ValueError(f"Not enough history for {state_name}. Need at least 24 rows.")

    model = ARIMA(y, order=order)
    fitted = model.fit()
    zhvi_forecast = fitted.forecast(steps=horizon)

    latest_row = state_df.iloc[-1]
    mortgage_rate = float(latest_row["mortgage_rate"])
    median_income = float(latest_row["median_household_income"])

    tax_rate = TAX_RATES.get(state_name, 0.012)
    insurance_rate = INSURANCE_RATE

    forecast_dates = pd.date_range(
        last_date + pd.offsets.MonthEnd(1),
        periods=horizon,
        freq="ME"
    )

    rows = []
    for dt, zhvi_val in zip(forecast_dates, zhvi_forecast):
        loan_amount = zhvi_val * (1 - 0.20)
        payment = monthly_payment(loan_amount, mortgage_rate)
        
        monthly_tax = zhvi_val * tax_rate / 12
        monthly_insurance = zhvi_val * insurance_rate / 12
        payment += monthly_tax + monthly_insurance

        monthly_income = median_income / 12
        affordability_ratio = monthly_income / payment if payment and payment > 0 else np.nan

        rows.append({
            "state": state_name,
            "date": dt,
            "forecast_home_price": float(zhvi_val),
            "forecast_affordability_ratio": float(affordability_ratio),
            "mortgage_rate_assumption": mortgage_rate,
            "income_assumption": median_income,
            "model": f"ARIMA{order}"
        })

    return pd.DataFrame(rows)


def run_forecasts():
    df = pd.read_csv(INPUT_FILE)
    df["date"] = pd.to_datetime(df["date"])

    all_forecasts = []
    failed_states = []

    for state, g in df.groupby("state"):
        try:
            fc = forecast_one_state(g, horizon=FORECAST_HORIZON, order=ARIMA_ORDER)
            all_forecasts.append(fc)
            print(f"Forecast completed for {state}")
        except Exception as e:
            failed_states.append((state, str(e)))
            print(f"Forecast failed for {state}: {e}")

    if not all_forecasts:
        raise ValueError("No forecasts were successfully created.")

    forecast_df = pd.concat(all_forecasts, ignore_index=True)
    forecast_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved forecast file to: {OUTPUT_FILE}")
    print(f"Rows: {len(forecast_df):,}")
    print(f"Columns: {len(forecast_df.columns):,}")

    if failed_states:
        print("\nStates with forecast errors:")
        for state, err in failed_states:
            print(f"- {state}: {err}")


if __name__ == "__main__":
    run_forecasts()