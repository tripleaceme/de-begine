"""Transform raw products into staging-ready records."""

import pandas as pd
from sqlalchemy import text

from config.settings import RAW_TABLES, STAGING_TABLES


def transform(engine):
    """
    Read all products from raw, deduplicate, clean, and upsert to staging.
    """
    df = pd.read_sql(text(f"SELECT * FROM {RAW_TABLES['products']}"), engine)

    if df.empty:
        print("  ⊘ No products to transform")
        return

    # Deduplicate
    df = df.drop_duplicates(subset=["product_id"], keep="last")

    # Null handling
    df = df.dropna(subset=["product_id", "product_name"])
    df["category"] = df["category"].fillna("Uncategorized")
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)

    # Standardize
    df["product_name"] = df["product_name"].str.strip().str.title()
    df["category"] = df["category"].str.strip().str.title()

    # Upsert: delete existing, then insert
    with engine.begin() as conn:
        ids = tuple(df["product_id"].tolist())
        # if len(ids) == 1:
        #     conn.execute(
        #         text(f"DELETE FROM {STAGING_TABLES['products']} WHERE product_id = :id"),
        #         {"id": ids[0]},
        #     )
        # elif ids:
        conn.execute(
            text(f"DELETE FROM {STAGING_TABLES['products']} WHERE product_id IN :ids"),
            {"ids": ids},
        )
        df.to_sql("products_clean", conn, schema="staging", if_exists="append", index=False)

    print(f"  ✓ Transformed {len(df)} products → staging")


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from config.settings import POSTGRES_URL
    transform(create_engine(POSTGRES_URL))

    
