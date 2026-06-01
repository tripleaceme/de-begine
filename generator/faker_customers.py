"""Generates synthetic customer records."""

import random
from datetime import datetime, timezone

from faker import Faker

#from config.settings import CUSTOMERS_MIN, CUSTOMERS_MAX
CUSTOMERS_MIN = 10
CUSTOMERS_MAX = 20

fake = Faker()


def introduce_bad_data(customer: dict) -> dict:
    """Introduce realistic data quality issues into customer records.
    
    Simulates common problems found in real data:
    - Missing emails (10% chance)
    - Invalid emails (8% chance)
    - Missing cities (5% chance)
    """
    if random.random() < 0.10:  # 10% missing email
        customer["email"] = None
    
    if random.random() < 0.08:  # 8% invalid email format
        customer["email"] = "invalid_email@@"
    
    if random.random() < 0.05:  # 5% missing city
        customer["city"] = ""
    
    return customer


def generate(batch_id: str) -> list[dict]:
    count = random.randint(CUSTOMERS_MIN, CUSTOMERS_MAX)
    customers = []

    for _ in range(count):
        customer = {
            "customer_id": f"CUST{random.randint(10000, 99999)}",
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "city": fake.city(),
            "batch_id": batch_id,
            "created_at": datetime.now(timezone.utc),
        }

        customer = introduce_bad_data(customer)
        customers.append(customer)

    return customers

print(generate("batch_001"))
