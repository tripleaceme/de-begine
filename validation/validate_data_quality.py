"""
Data quality contract validation.

Runs checks against ALL data in raw tables before it flows into staging.
Since raw tables are truncated after each transform, everything in raw
is from the current batch.

Checks:
  - order_id cannot be null
  - customer_id cannot be null on orders
  - product_id cannot be null on orders
  - amount must be positive
  - payment_status must match allowed values
  - batch_id must exist (source metadata)
"""

import psycopg2

from config.postgres_settings import POSTGRES_CONFIG
from config.generation_settings import PAYMENT_STATUSES


class ValidationError(Exception):
    """Raised when data quality checks fail."""
    pass


def validate():
    """
    Run all quality checks against raw tables.
    Raises ValidationError if any check fails.
    """
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    errors = []

    try:
        with conn.cursor() as cur:
            # ── order_id cannot be null ─────────────────────────
            cur.execute(
                "SELECT COUNT(*) FROM raw.orders_raw WHERE order_id IS NULL OR order_id = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} orders with null order_id")

            # ── customer_id cannot be null on orders ───────────
            cur.execute(
                "SELECT COUNT(*) FROM raw.orders_raw WHERE customer_id IS NULL OR customer_id = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} orders with null customer_id")

            # ── product_id cannot be null on orders ────────────
            cur.execute(
                "SELECT COUNT(*) FROM raw.orders_raw WHERE product_id IS NULL OR product_id = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} orders with null product_id")

            # ── amount must be positive and not NaN ──────────────
            cur.execute(
                "SELECT COUNT(*) FROM raw.orders_raw WHERE amount <> amount OR amount <= 0"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} orders with invalid amount")

            # ── payment_status must be valid ───────────────────
            allowed = tuple(PAYMENT_STATUSES)
            cur.execute(
                "SELECT DISTINCT payment_status FROM raw.orders_raw WHERE payment_status NOT IN %s",
                (allowed,),
            )
            invalid = [row[0] for row in cur.fetchall()]
            if invalid:
                errors.append(f"Invalid payment_status values: {invalid}")

            # ── batch_id must exist ────────────────────────────
            cur.execute(
                "SELECT COUNT(*) FROM raw.orders_raw WHERE batch_id IS NULL OR batch_id = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} orders with missing batch_id")

            # ── raw customers must have valid IDs, names, and emails ─
            cur.execute(
                "SELECT COUNT(*) FROM raw.customers_raw WHERE customer_id IS NULL OR customer_id = '' OR name IS NULL OR name = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} customers with missing customer_id or name")

            cur.execute(
                "SELECT COUNT(*) FROM raw.customers_raw WHERE email IS NOT NULL AND email <> '' AND (email NOT LIKE '%@%.%' OR email LIKE '%@%@%' OR email LIKE '% @%' OR email LIKE '%@.%' OR email LIKE '%.@%')"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} customers with invalid email format")

            cur.execute(
                "SELECT COUNT(*) FROM raw.customers_raw WHERE city IS NULL OR city = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} customers with missing city")

            # ── raw products must have valid IDs, names, and prices ───
            cur.execute(
                "SELECT COUNT(*) FROM raw.products_raw WHERE product_id IS NULL OR product_id = '' OR product_name IS NULL OR product_name = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} products with missing product_id or product_name")

            cur.execute(
                "SELECT COUNT(*) FROM raw.products_raw WHERE price IS NULL OR price <= 0 OR price >= 100000"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} products with invalid price")

            cur.execute(
                "SELECT COUNT(*) FROM raw.products_raw WHERE batch_id IS NULL OR batch_id = ''"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} products with missing batch_id")

    finally:
        conn.close()

    if errors:
        error_msg = "Data validation failed:\n" + "\n".join(f"  ✗ {e}" for e in errors)
        print(error_msg)
        raise ValidationError(error_msg)

    print("  ✓ All validation checks passed")


if __name__ == "__main__":
    validate()
