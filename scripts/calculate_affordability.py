from pathlib import Path
import pandas as pd
import numpy as np

INPUT_FILE = Path("data/processed/housing_dataset.csv")
OUTPUT_FILE = Path("data/processed/housing_with_affordability.csv")

def calculate_affordability():

    df = pd.read_csv(INPUT_FILE)

    # Monthly mortgage rate
    df["monthly_rate"] = df["mortgage_rate"] / 100 / 12

    # Loan assumptions
    loan_term_months = 30 * 12
    down_payment = 0.20

    # Loan amount
    df["loan_amount"] = df["zhvi"] * (1 - down_payment)

    # Monthly mortgage payment formula
    r = df["monthly_rate"]
    n = loan_term_months

    df["monthly_payment"] = (
        df["loan_amount"] *
        (r * (1 + r)**n) /
        ((1 + r)**n - 1)
    )

    # Add rough property tax + insurance (estimate)
    df["monthly_payment"] += df["zhvi"] * 0.012 / 12  # ~1.2% annual

    # Monthly income
    df["monthly_income"] = df["median_household_income"] / 12

    # Affordability ratio
    df["affordability_ratio"] = df["monthly_income"] / df["monthly_payment"]

    # Clean up
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["affordability_ratio"])

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved affordability dataset to: {OUTPUT_FILE}")
    print(df[["state", "date", "affordability_ratio"]].head())

if __name__ == "__main__":
    calculate_affordability()