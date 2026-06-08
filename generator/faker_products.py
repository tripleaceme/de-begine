"""Generates synthetic product records."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timezone

from config.settings import PRODUCTS_MIN, PRODUCTS_MAX, PRODUCT_CATEGORIES


def introduce_bad_product_data(product: dict, all_categories: list) -> dict:
    """Introduce simple product data quality issues for realistic test data."""
    if random.random() < 0.08:  # 8% missing product name
        product["product_name"] = None

    if random.random() < 0.06:  # 6% invalid price values
        product["price"] = round(random.uniform(100000, 999999), 2)

    if random.random() < 0.05:  # 5% zero-price bug
        product["price"] = 0

    if random.random() < 0.05:  # 5% category mismatch
        product["category"] = random.choice(all_categories)

    if random.random() < 0.05:  # 5% schema drift adds unexpected fields
        product["brand"] = random.choice(["Nike", "Apple", "Samsung", "Sony", "Generic"])
        product["is_active"] = random.choice([True, False])

    return product




def generate_products(batch_id: str) -> list[dict]:
    count = random.randint(PRODUCTS_MIN, PRODUCTS_MAX)
    products_data = []

    all_categories = list(PRODUCT_CATEGORIES.keys())

    for _ in range(count):
        category = random.choice(all_categories)

        new_product = {
            "product_id": f"PROD{random.randint(1000, 9999)}",
            "product_name": random.choice(PRODUCT_CATEGORIES[category]),
            "category": category,
            "price": round(random.uniform(50, 1500), 2),
            "batch_id": batch_id,
            "created_at": datetime.now(timezone.utc),
        }

        bad_product_data = introduce_bad_product_data(new_product, all_categories)
        products_data.append(bad_product_data)

    return products_data