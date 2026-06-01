"""Transform raw customers into staging-ready records."""

import pandas as pd
from sqlalchemy import text

from config.settings import RAW_TABLES, STAGING_TABLES


def transform(engine):
    """
    Read all customers from raw, deduplicate, clean, and upsert to staging.
    """
    df = pd.read_sql(f"SELECT * FROM {RAW_TABLES['customers']}", engine)

    if df.empty:
        print("  ⊘ No customers to transform")
        return

    # Deduplicate on customer_id
    df = df.drop_duplicates(subset=["customer_id"], keep="last")

    # Null handling
    df = df.dropna(subset=["customer_id", "name"])
    df["email"] = df["email"].fillna("").astype(str).str.strip().str.lower()
    df["email"] = df["email"].where(
        df["email"].str.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
        "unknown@example.com",
    )
    df["email"] = df["email"].replace({"": "unknown@example.com"})
    df["phone"] = df["phone"].fillna("N/A")
    df["city"] = df["city"].fillna("").astype(str).str.strip()
    df["city"] = df["city"].replace({"": "Unknown"})

    # Standardize
    df["name"] = df["name"].str.strip().str.title()
    df["city"] = df["city"].str.title()
    df["email"] = df["email"].str.strip().str.lower()

    # Upsert: delete existing, then insert
    with engine.begin() as conn:
        ids = tuple(df["customer_id"].tolist())
        if len(ids) == 1:
            conn.execute(
                text(f"DELETE FROM {STAGING_TABLES['customers']} WHERE customer_id = :id"),
                {"id": ids[0]},
            )
        elif ids:
            conn.execute(
                text(f"DELETE FROM {STAGING_TABLES['customers']} WHERE customer_id IN :ids"),
                {"ids": ids},
            )
        df.to_sql("customers_clean", conn, schema="staging", if_exists="append", index=False)

    print(f"  ✓ Transformed {len(df)} customers → staging")


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from config.settings import POSTGRES_URL
    transform(create_engine(POSTGRES_URL))
