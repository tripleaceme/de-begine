# generator/data_quality.py

import random


def maybe(probability: float) -> bool:
    return random.random() < probability


def introduce_customer_issues(customer: dict, config: dict) -> dict:
    if maybe(config["missing_email_rate"]):
        customer["email"] = None

    if maybe(config["invalid_email_rate"]):
        customer["email"] = "invalid_email@@"

    if maybe(config["missing_city_rate"]):
        customer["city"] = ""

    return customer


def introduce_order_issues(order: dict, config: dict) -> dict:
    if maybe(config["missing_product_rate"]):
        order["product_id"] = None

    if maybe(config["invalid_amount_rate"]):
        order["amount"] = "NaN"

    if maybe(config["negative_amount_rate"]):
        order["amount"] = -abs(order["amount"])

    if maybe(config["invalid_status_rate"]):
        order["payment_status"] = "UNKNOWN_STATUS"

    return order
