"""Transform raw orders into staging-ready records."""

import pandas as pd
from sqlalchemy import text

from config.settings import RAW_TABLES, STAGING_TABLES


def transform(engine):
    """
    Read all orders from raw, deduplicate, clean, and upsert to staging.
    """
    df = pd.read_sql(f"SELECT * FROM {RAW_TABLES['orders']}", engine)

    if df.empty:
        print("  ⊘ No orders to transform")
        return

    # Deduplicate on order_id
    df = df.drop_duplicates(subset=["order_id"], keep="last")

    # Null handling
    df = df.dropna(subset=["order_id", "customer_id", "product_id"])

    # Type corrections
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    # Standardize
    df["region"] = df["region"].str.strip().str.title()
    df["payment_status"] = df["payment_status"].str.strip().str.lower()

    # Filter invalid payment statuses
    valid_statuses = {"paid", "failed", "pending"}
    df = df[df["payment_status"].isin(valid_statuses)]

    # Upsert: delete existing, then insert (chunked for large batches)
    with engine.begin() as conn:
        ids = tuple(df["order_id"].tolist())
        if len(ids) == 1:
            conn.execute(
                text(f"DELETE FROM {STAGING_TABLES['orders']} WHERE order_id = :id"),
                {"id": ids[0]},
            )
        elif ids:
            for i in range(0, len(ids), 500):
                chunk = ids[i : i + 500]
                conn.execute(
                    text(f"DELETE FROM {STAGING_TABLES['orders']} WHERE order_id IN :ids"),
                    {"ids": chunk},
                )
        df.to_sql("orders_clean", conn, schema="staging", if_exists="append", index=False)

    print(f"  ✓ Transformed {len(df)} orders → staging")


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from config.settings import POSTGRES_URL
    transform(create_engine(POSTGRES_URL))
