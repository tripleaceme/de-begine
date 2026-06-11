"""
Synthetic-data generation settings and batch helpers.

Pure configuration constants and date helpers — no external service
credentials, so this module imports with zero env vars set.
"""

import os
from datetime import datetime, timezone

from config import env  # noqa: F401  (loads .env once, for its side effect)


# ── Source generation volumes ──────────────────────────────────
ORDERS_MIN = 2000
ORDERS_MAX = 5000
CUSTOMERS_MIN = 10
CUSTOMERS_MAX = 20
PRODUCTS_MIN = 5
PRODUCTS_MAX = 10

REGIONS = ["Mandera East", "Mandera West", "Mandera Central"]
PAYMENT_STATUSES = ["paid", "failed", "pending"]

PRODUCT_CATEGORIES = {
    "Electronics": [
        "Wireless Earbuds", "Power Bank", "USB-C Hub", "Bluetooth Speaker",
        "Smart Watch", "Laptop Stand", "Webcam", "Portable SSD",
        "Phone Case", "Screen Protector",
    ],
    "Groceries": [
        "Rice 5kg", "Cooking Oil 3L", "Sugar 2kg", "Maize Flour 2kg",
        "Tea Leaves 500g", "Milk Powder 900g", "Salt 1kg",
        "Wheat Flour 2kg", "Pasta 500g", "Tomato Paste",
    ],
    "Clothing": [
        "Cotton T-Shirt", "Denim Jeans", "Polo Shirt", "Hoodie",
        "Khaki Trousers", "Sports Shorts", "Formal Shirt",
        "Beanie Hat", "Canvas Shoes", "Leather Belt",
    ],
    "Home & Kitchen": [
        "Water Bottle", "Thermos Flask", "Frying Pan", "Dinner Set",
        "Storage Container", "Cutting Board", "Blender",
        "Kettle", "Mop Set", "Towel Set",
    ],
}


# ── Batch scheduling ───────────────────────────────────────────
NUMBER_OF_BATCHES = int(os.getenv("NUMBER_OF_BATCHES", "1"))

# Scheduled run hours (UTC) — must match .github/workflows/generate_data.yml cron
BATCH_SCHEDULE_HOURS = [7, 15]


def generate_batch_id() -> str:
    """
    Auto-generate batch ID: 2026_03_23_07_batch_01

    date_part: YYYY_MM_DD
    hour: HH (24-hour format)
    batch_number: 1 or 2 based on which scheduled hour is closest (7 or 15 UTC)

    Determines the batch number based on which scheduled hour slot
    the current time falls closest to. Falls back to sequential
    numbering if the hour doesn't match a known schedule.
    """
    now = datetime.now(timezone.utc)
    date_part = now.strftime("%Y_%m_%d")
    hour = now.hour

    # Find the closest scheduled hour to determine batch number
    batch_number = 1
    for i, scheduled_hour in enumerate(BATCH_SCHEDULE_HOURS):
        if abs(hour - scheduled_hour) <= 1:
            batch_number = i + 1
            break
    else:
        # Manual run outside scheduled hours — assign based on AM/PM
        batch_number = 1 if hour < 12 else 2

    return f"{date_part}_{hour:02d}_batch_0{batch_number}"
