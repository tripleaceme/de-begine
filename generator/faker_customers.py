"""Generates synthetic customer records."""

import random
from datetime import datetime, timezone

from faker import Faker

from config.settings import CUSTOMERS_MIN, CUSTOMERS_MAX
from config.data_quality import DATA_QUALITY_PROFILE
from generator.data_quality import introduce_customer_issues

fake = Faker()


def generate(batch_id: str) -> list[dict]:
    count = random.randint(CUSTOMERS_MIN, CUSTOMERS_MAX)
    customers = []

    config = DATA_QUALITY_PROFILE["customers"]

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

        customer = introduce_customer_issues(customer, config)
        customers.append(customer)

    return customers