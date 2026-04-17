"""
Extracts today's records from MongoDB and loads them into
PostgreSQL raw landing tables.

Raw tables act as a stateless buffer — data flows in,
gets validated and transformed, then the buffer is truncated.
"""

from datetime import datetime, timezone, timedelta

import psycopg2
import psycopg2.extras
from pymongo import MongoClient

from config.settings import (
    MONGO_URI,
    MONGO_DB,
    MONGO_COLLECTIONS,
    POSTGRES_CONFIG,
    RAW_TABLES,
    TABLE_COLUMNS,
)

# Column order for each raw table


def _get_today_date_range(target_date=None):
    """Get start and end datetime for today (UTC), or specified date."""
    if target_date is None:
        now = datetime.now(timezone.utc)
    else:
        now = target_date.replace(tzinfo=timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today = start_of_today + timedelta(days=1)
    return start_of_today, end_of_today


def _serialize_value(value):
    """Convert MongoDB types to Postgres-compatible values."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def extract_to_postgres(target_date=None) -> dict:
    """
    Pull today's docs from MongoDB and insert into raw tables.
    Returns source_rows and loaded_rows per collection.
    """
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    conn = psycopg2.connect(**POSTGRES_CONFIG)

    start_of_today, end_of_today = _get_today_date_range(target_date)
    counts = {}

    try:
        for name, collection_name in MONGO_COLLECTIONS.items():
            # Filter for documents created today only
            query = {"created_at": {"$gte": start_of_today, "$lt": end_of_today}}
            docs = list(db[collection_name].find(query))
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

            loaded_rows = len(rows)
            print(f"  ✓ Staged {loaded_rows} {name} for {RAW_TABLES[name]}")
            counts[name] = {"source_rows": source_rows, "loaded_rows": loaded_rows}

        # Atomic commit: all collections land together, or none do.
        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        client.close()
        conn.close()

    return counts


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target_date = datetime.fromisoformat(sys.argv[1])
        counts = extract_to_postgres(target_date)
    else:
        counts = extract_to_postgres()
    print(f"\n✓ Extraction complete. {counts}")
