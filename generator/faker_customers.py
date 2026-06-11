"""Generates synthetic customer records."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timezone

from faker import Faker

from config.generation_settings import CUSTOMERS_MIN, CUSTOMERS_MAX

fake = Faker()


def introduce_bad_customer_data(customer: dict) -> dict:
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


def generate_customers(batch_id: str) -> list[dict]:
    count = random.randint(CUSTOMERS_MIN, CUSTOMERS_MAX)
    customers_data = []

    for _ in range(count):
        new_customer_data = {
            "customer_id": f"CUST{random.randint(10000, 99999)}",
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "city": fake.city(),
            "batch_id": batch_id,
            "created_at": datetime.now(timezone.utc),
        }

        bad_customer_data = introduce_bad_customer_data(new_customer_data)
        customers_data.append(bad_customer_data)

    return customers_data
