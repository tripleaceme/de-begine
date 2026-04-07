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

from config.settings import POSTGRES_CONFIG, PAYMENT_STATUSES


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

            # ── amount must be positive ────────────────────────
            cur.execute(
                "SELECT COUNT(*) FROM raw.orders_raw WHERE amount <= 0"
            )
            count = cur.fetchone()[0]
            if count > 0:
                errors.append(f"Found {count} orders with non-positive amount")

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

    finally:
        conn.close()

    if errors:
        error_msg = "Data validation failed:\n" + "\n".join(f"  ✗ {e}" for e in errors)
        print(error_msg)
        raise ValidationError(error_msg)

    print("  ✓ All validation checks passed")


if __name__ == "__main__":
    validate()
