"""
Extracts all records from MongoDB and loads them into
PostgreSQL raw landing tables.

Raw tables act as a stateless buffer — data flows in,
gets validated and transformed, then the buffer is truncated.
"""

from datetime import datetime

import psycopg2
import psycopg2.extras
from pymongo import MongoClient

from config.mongo_settings import MONGO_URI, MONGO_DB, MONGO_COLLECTIONS
from config.postgres_settings import POSTGRES_CONFIG, RAW_TABLES

# Column order for each raw table
TABLE_COLUMNS = {
    "customers": [
        "customer_id", "name", "email", "phone", "city", "batch_id", "created_at",
    ],
    "products": [
        "product_id", "product_name", "category", "price", "batch_id", "created_at",
    ],
    "orders": [
        "order_id", "customer_id", "product_id", "region", "amount",
        "payment_status", "batch_id", "created_at",
    ],
}


def _serialize_value(value):
    """Convert MongoDB types to Postgres-compatible values."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def extract_to_postgres() -> dict:
    """
    Pull all docs from MongoDB and insert into raw tables.
    Returns source_rows and loaded_rows per collection.
    """
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    conn = psycopg2.connect(**POSTGRES_CONFIG)

    counts = {}

    try:
        for name, collection_name in MONGO_COLLECTIONS.items():
            docs = list(db[collection_name].find())
            source_rows = len(docs)

            if not docs:
                counts[name] = {"source_rows": 0, "loaded_rows": 0}
                continue

            columns = TABLE_COLUMNS[name]
            col_names = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))
            insert_sql = f"INSERT INTO {RAW_TABLES[name]} ({col_names}) VALUES ({placeholders})"

            rows = []
            for doc in docs:
                row = tuple(_serialize_value(doc.get(col)) for col in columns)
                rows.append(row)

            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, insert_sql, rows, page_size=500)
            conn.commit()

            loaded_rows = len(rows)
            print(f"  ✓ Loaded {loaded_rows} {name} into {RAW_TABLES[name]}")
            counts[name] = {"source_rows": source_rows, "loaded_rows": loaded_rows}

    finally:
        client.close()
        conn.close()

    return counts


if __name__ == "__main__":
    counts = extract_to_postgres()
    print(f"\n✓ Extraction complete. {counts}")
