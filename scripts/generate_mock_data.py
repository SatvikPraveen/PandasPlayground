import pandas as pd
import numpy as np
import json
from pathlib import Path
from faker import Faker

fake = Faker()
np.random.seed(42)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

NUM_ROWS = 10000

# ------------------------------------
# 1. 🌦 Weather Data (JSON)
# ------------------------------------
dates = pd.date_range(start="2022-01-01", periods=NUM_ROWS)
conditions = ["Sunny", "Rain", "Cloudy", "Storm", "Snow"]

weather_data = [
    {
        "date": str(date.date()),
        "temperature_c": np.random.randint(-10, 40),
        "humidity": np.random.randint(30, 100),
        "condition": np.random.choice(conditions)
    }
    for date in dates
]

with open(DATA_DIR / "weather_data.json", "w") as f:
    json.dump(weather_data, f, indent=2)

print("✅ 10000-row weather_data.json created.")

# ------------------------------------
# 2. 🏦 Bank Loan Data (Excel)
# ------------------------------------
loan_purposes = ["Car", "Home", "Education", "Business", "Medical", "Vacation"]
approvals = ["Yes", "No"]

loan_data = pd.DataFrame({
    "Customer_ID": range(1001, 1001 + NUM_ROWS),
    "Customer_Name": [fake.name() for _ in range(NUM_ROWS)],
    "Age": np.random.randint(21, 65, size=NUM_ROWS),
    "Income": np.random.randint(25000, 150000, size=NUM_ROWS),
    "Loan_Amount": np.random.randint(3000, 80000, size=NUM_ROWS),
    "Loan_Purpose": np.random.choice(loan_purposes, size=NUM_ROWS),
    "Approved": np.random.choice(approvals, size=NUM_ROWS)
})

loan_data.to_excel(DATA_DIR / "bank_loans.xlsx", index=False)
print("✅ 10000-row bank_loans.xlsx created.")

# ------------------------------------
# 3. 🧬 COVID Data (Parquet)
# ------------------------------------
countries = ["USA", "India", "Brazil", "Germany", "Canada"]
variants = ["Alpha", "Delta", "Omicron", "BA.5", "XBB"]

covid_data = pd.DataFrame({
    "date": pd.date_range(start="2020-01-01", periods=NUM_ROWS),
    "country": np.random.choice(countries, size=NUM_ROWS),
    "variant": np.random.choice(variants, size=NUM_ROWS),
    "new_cases": np.random.poisson(500, size=NUM_ROWS),
    "new_deaths": np.random.poisson(10, size=NUM_ROWS),
    "hospitalized": np.random.randint(0, 5000, size=NUM_ROWS)
})

covid_data.to_parquet(DATA_DIR / "covid_data.parquet", index=False)
print("✅ 10000-row covid_data.parquet created.")

# ------------------------------------
# 4. 🧾 Bank Loan Data - Multi-Sheet Excel
# ------------------------------------
with pd.ExcelWriter(DATA_DIR / "bank_loans_multisheet.xlsx") as writer:
    for region in ["East", "West", "North", "South"]:
        temp_df = loan_data.copy()
        temp_df["Region"] = region
        temp_df.to_excel(writer, sheet_name=region, index=False)

print("✅ bank_loans_multisheet.xlsx with 4 regions created.")

# ------------------------------------
# 5. 📦 Superstore Sales Data (CSV)
# ------------------------------------
regions = ["East", "West", "Central", "South"]
segments = ["Consumer", "Corporate", "Home Office"]
categories = {
    "Furniture": ["Bookcases", "Chairs", "Tables"],
    "Office Supplies": ["Binders", "Pens", "Paper", "Labels"],
    "Technology": ["Phones", "Accessories", "Copiers", "Machines"]
}

product_list = []
for category, subcats in categories.items():
    for sub in subcats:
        for i in range(5):
            product_list.append((category, sub, f"{sub} Model {i+1}"))

superstore_data = pd.DataFrame({
    "Order ID": [f"ORD-{i+10000}" for i in range(NUM_ROWS)],
    "Customer ID": [f"CUST-{np.random.randint(1000, 9999)}" for _ in range(NUM_ROWS)],
    "Customer Name": [fake.name() for _ in range(NUM_ROWS)],
    "Segment": np.random.choice(segments, size=NUM_ROWS),
    "Region": np.random.choice(regions, size=NUM_ROWS),
    "Order Date": pd.date_range(start="2020-01-01", periods=NUM_ROWS),
    "Ship Date": pd.date_range(start="2020-01-03", periods=NUM_ROWS),
}, dtype=str)

# Add Category, Sub-Category, Product
categories_sampled = [product_list[i % len(product_list)] for i in range(NUM_ROWS)]
superstore_data["Category"] = [cat for cat, sub, prod in categories_sampled]
superstore_data["Sub-Category"] = [sub for cat, sub, prod in categories_sampled]
superstore_data["Product Name"] = [prod for cat, sub, prod in categories_sampled]

# Add Numeric Fields
superstore_data["Sales"] = np.round(np.random.uniform(10.0, 2000.0, size=NUM_ROWS), 2)
superstore_data["Quantity"] = np.random.randint(1, 10, size=NUM_ROWS)
superstore_data["Discount"] = np.round(np.random.choice([0.0, 0.1, 0.2, 0.3, 0.5], size=NUM_ROWS), 2)
superstore_data["Profit"] = np.round(superstore_data["Sales"] * (0.05 + np.random.randn(NUM_ROWS) * 0.05), 2)

# Save to CSV
superstore_data.to_csv(DATA_DIR / "superstore_sales.csv", index=False)
print("✅ 10000-row superstore_sales.csv created.")