from pathlib import Path
import pandas as pd
import numpy as np

INPUT_FILE = Path("data/processed/housing_dataset.csv")
OUTPUT_FILE = Path("data/processed/housing_with_affordability.csv")

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

def calculate_affordability():
    df = pd.read_csv(INPUT_FILE)

    df["monthly_rate"] = df["mortgage_rate"] / 100 / 12
    loan_term_months = 30 * 12
    down_payment = 0.20

    df["loan_amount"] = df["zhvi"] * (1 - down_payment)

    r = df["monthly_rate"]
    n = loan_term_months

    df["monthly_payment"] = (
        df["loan_amount"] *
        (r * (1 + r)**n) /
        ((1 + r)**n - 1)
    )

    df["tax_rate"] = df["state"].map(TAX_RATES)
    df["insurance_rate"] = INSURANCE_RATE

    df["monthly_tax"] = df["zhvi"] * df["tax_rate"] / 12
    df["monthly_insurance"] = df["zhvi"] * df["insurance_rate"] / 12

    df["monthly_payment"] = (
        df["monthly_payment"] +
        df["monthly_tax"] +
        df["monthly_insurance"]
    )

    df["monthly_income"] = df["median_household_income"] / 12
    df["affordability_ratio"] = df["monthly_income"] / df["monthly_payment"]

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["affordability_ratio"])

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved affordability dataset to: {OUTPUT_FILE}")
    print(df[["state", "date", "tax_rate", "insurance_rate", "affordability_ratio"]].head())

if __name__ == "__main__":
    calculate_affordability()
