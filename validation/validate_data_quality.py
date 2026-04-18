"""
Data quality observability.

Runs checks against ALL data in raw tables before it flows into staging,
then writes a row per check to monitoring.data_quality_log. The batch is
never blocked — transforms are responsible for dropping invalid rows via
dropna; this module's job is to make source-data degradation visible and
queryable over time.

Checks:
  Customers:
    - customers.null_customer_id
    - customers.null_name
    - customers.missing_batch_id
  Products:
    - products.null_product_id
    - products.null_product_name
    - products.invalid_price    (null or <= 0)
    - products.missing_batch_id
  Orders:
    - orders.null_order_id
    - orders.null_customer_id
    - orders.null_product_id
    - orders.invalid_amount     (null or <= 0)
    - orders.null_payment_status
    - orders.invalid_payment_status
    - orders.missing_batch_id
"""

from datetime import datetime, timezone

import psycopg2

from config.settings import POSTGRES_CONFIG, PAYMENT_STATUSES


def _count_null_or_empty(cur, table: str, column: str) -> int:
    cur.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL OR {column} = ''"
    )
    return cur.fetchone()[0]


def _count(cur, sql: str) -> int:
    cur.execute(sql)
    return cur.fetchone()[0]


def validate():
    """
    Run all quality checks against raw tables, log counts to monitoring,
    and print a summary. Never raises — transforms handle row-level cleanup.
    """
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    results = []  # list of (check_name, failed_count, detail)

    try:
        with conn.cursor() as cur:
            # ── Customers ──────────────────────────────────────
            results.append((
                "customers.null_customer_id",
                _count_null_or_empty(cur, "raw.customers_raw", "customer_id"),
                None,
            ))
            results.append((
                "customers.null_name",
                _count_null_or_empty(cur, "raw.customers_raw", "name"),
                None,
            ))
            results.append((
                "customers.missing_batch_id",
                _count_null_or_empty(cur, "raw.customers_raw", "batch_id"),
                None,
            ))

            # ── Products ───────────────────────────────────────
            results.append((
                "products.null_product_id",
                _count_null_or_empty(cur, "raw.products_raw", "product_id"),
                None,
            ))
            results.append((
                "products.null_product_name",
                _count_null_or_empty(cur, "raw.products_raw", "product_name"),
                None,
            ))
            results.append((
                "products.invalid_price",
                _count(cur, "SELECT COUNT(*) FROM raw.products_raw WHERE price IS NULL OR price <= 0"),
                None,
            ))
            results.append((
                "products.missing_batch_id",
                _count_null_or_empty(cur, "raw.products_raw", "batch_id"),
                None,
            ))

            # ── Orders ─────────────────────────────────────────
            results.append((
                "orders.null_order_id",
                _count_null_or_empty(cur, "raw.orders_raw", "order_id"),
                None,
            ))
            results.append((
                "orders.null_customer_id",
                _count_null_or_empty(cur, "raw.orders_raw", "customer_id"),
                None,
            ))
            results.append((
                "orders.null_product_id",
                _count_null_or_empty(cur, "raw.orders_raw", "product_id"),
                None,
            ))
            results.append((
                "orders.invalid_amount",
                _count(cur, "SELECT COUNT(*) FROM raw.orders_raw WHERE amount IS NULL OR amount <= 0"),
                None,
            ))
            results.append((
                "orders.null_payment_status",
                _count(cur, "SELECT COUNT(*) FROM raw.orders_raw WHERE payment_status IS NULL"),
                None,
            ))

            allowed = tuple(PAYMENT_STATUSES)
            cur.execute(
                "SELECT payment_status, COUNT(*) FROM raw.orders_raw "
                "WHERE payment_status IS NOT NULL AND payment_status NOT IN %s "
                "GROUP BY payment_status",
                (allowed,),
            )
            invalid_rows = cur.fetchall()
            invalid_total = sum(count for _, count in invalid_rows)
            invalid_detail = (
                ", ".join(f"{status}={count}" for status, count in invalid_rows)
                if invalid_rows else None
            )
            results.append((
                "orders.invalid_payment_status",
                invalid_total,
                invalid_detail,
            ))

            results.append((
                "orders.missing_batch_id",
                _count_null_or_empty(cur, "raw.orders_raw", "batch_id"),
                None,
            ))

            # ── Write all results in one transaction ───────────
            cur.executemany(
                """
                INSERT INTO monitoring.data_quality_log
                    (run_id, check_name, failed_count, detail)
                VALUES (%s, %s, %s, %s)
                """,
                [(run_id, name, count, detail) for name, count, detail in results],
            )
        conn.commit()
    finally:
        conn.close()

    # ── Console summary (visible in task logs) ────────────────
    failures = [(name, count, detail) for name, count, detail in results if count > 0]
    total_failures = sum(count for _, count, _ in failures)

    if failures:
        print(f"  ⚠ Data quality issues logged (run: {run_id}, {total_failures} bad rows across {len(failures)} rules):")
        for name, count, detail in failures:
            suffix = f" [{detail}]" if detail else ""
            print(f"    ⚠ {name}: {count}{suffix}")
    else:
        print(f"  ✓ All data quality checks passed (run: {run_id})")


if __name__ == "__main__":
    validate()
