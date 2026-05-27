"""
Generates a realistic sample sales dataset for demo purposes.
Run once: python generate_sample_data.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

PRODUCTS = {
    "Laptop Pro":    {"base_price": 1200, "category": "Electronics"},
    "Wireless Mouse":{"base_price": 35,   "category": "Accessories"},
    "USB-C Hub":     {"base_price": 55,   "category": "Accessories"},
    "Monitor 27\"":  {"base_price": 380,  "category": "Electronics"},
    "Mechanical Keyboard": {"base_price": 150, "category": "Accessories"},
    "Webcam HD":     {"base_price": 90,   "category": "Electronics"},
    "Desk Lamp LED": {"base_price": 45,   "category": "Office"},
    "Ergonomic Chair":{"base_price": 450, "category": "Office"},
    "Notebook Set":  {"base_price": 20,   "category": "Stationery"},
    "Pen Pack":      {"base_price": 12,   "category": "Stationery"},
}

REGIONS   = ["North", "South", "East", "West", "Central"]
CHANNELS  = ["Online", "In-Store", "Reseller"]
SALESREPS = ["Alice", "Bob", "Carol", "David", "Emma", "Frank"]

START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2024, 12, 31)
NUM_ROWS   = 1000

rows = []
for _ in range(NUM_ROWS):
    product_name = random.choice(list(PRODUCTS.keys()))
    product      = PRODUCTS[product_name]
    date         = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))
    units        = random.randint(1, 20)
    discount_pct = random.choice([0, 0, 0, 5, 10, 15, 20])
    unit_price   = product["base_price"] * (1 - discount_pct / 100)
    revenue      = round(units * unit_price, 2)
    # Add some seasonal effect: higher sales in Q4
    if date.month in [11, 12]:
        units    = int(units * 1.5)
        revenue  = round(units * unit_price, 2)

    rows.append({
        "date":         date.strftime("%Y-%m-%d"),
        "product":      product_name,
        "category":     product["category"],
        "region":       random.choice(REGIONS),
        "channel":      random.choice(CHANNELS),
        "sales_rep":    random.choice(SALESREPS),
        "units_sold":   units,
        "unit_price":   round(unit_price, 2),
        "discount_pct": discount_pct,
        "revenue":      revenue,
    })

df = pd.DataFrame(rows)
df = df.sort_values("date").reset_index(drop=True)
df.to_csv("sales_data.csv", index=False)
print(f"Generated sales_data.csv with {len(df)} rows")
print(df.head())
