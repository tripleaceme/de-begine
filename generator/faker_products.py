"""Generates synthetic product records."""

import random
from datetime import datetime, timezone

from config.settings import PRODUCTS_MIN, PRODUCTS_MAX, PRODUCT_CATEGORIES


def introduce_product_bad_data(product: dict, all_categories: list) -> dict:
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


def generate(batch_id: str) -> list[dict]:
    count = random.randint(PRODUCTS_MIN, PRODUCTS_MAX)
    products = []

    all_categories = list(PRODUCT_CATEGORIES.keys())

    for _ in range(count):
        category = random.choice(all_categories)

        product = {
            "product_id": f"PROD{random.randint(1000, 9999)}",
            "product_name": random.choice(PRODUCT_CATEGORIES[category]),
            "category": category,
            "price": round(random.uniform(50, 15000), 2),
            "batch_id": batch_id,
            "created_at": datetime.now(timezone.utc),
        }

        product = introduce_product_bad_data(product, all_categories)
        products.append(product)

    return products
    
# def generate(batch_id: str) -> list[dict]:
#     """Generate 5-10 product documents."""
#     count = random.randint(PRODUCTS_MIN, PRODUCTS_MAX)
#     products = []

#     for _ in range(count):
#         category = random.choice(list(PRODUCT_CATEGORIES.keys()))
#         products.append({
#             "product_id": f"PROD{random.randint(1000, 9999)}",
#             "product_name": random.choice(PRODUCT_CATEGORIES[category]),
#             "category": category,
#             "price": round(random.uniform(50, 15000), 2),
#             "batch_id": batch_id,
#             "created_at": datetime.now(timezone.utc),
#         })

#     return products
