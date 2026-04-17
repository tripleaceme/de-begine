"""
Extracts today's records from MongoDB and writes them as JSON
to MinIO under date-partitioned paths (YYYY/MM/DD/).

MinIO serves as the durable archive — if anything fails downstream,
you can always replay from here.
"""

import json
from datetime import datetime, timezone, timedelta

import boto3
from pymongo import MongoClient

from config.settings import (
    MONGO_URI,
    MONGO_DB,
    MONGO_COLLECTIONS,
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET,
    today_partition,
)


def _get_today_date_range(target_date=None):
    """Get start and end datetime for today (UTC), or specified date."""
    if target_date is None:
        now = datetime.now(timezone.utc)
    else:
        now = target_date.replace(tzinfo=timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today = start_of_today + timedelta(days=1)
    return start_of_today, end_of_today


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )


def _ensure_bucket(s3):
    try:
        s3.head_bucket(Bucket=MINIO_BUCKET)
    except s3.exceptions.ClientError:
        s3.create_bucket(Bucket=MINIO_BUCKET)
        print(f"  ✓ Created bucket: {MINIO_BUCKET}")


def _serialize_doc(doc: dict) -> dict:
    """Remove MongoDB _id and convert datetimes to ISO strings."""
    doc.pop("_id", None)
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc


def extract_to_minio(target_date=None) -> dict:
    """
    Pull today's docs from MongoDB and write to MinIO.
    Returns row counts per collection.
    """
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    s3 = _get_s3_client()
    _ensure_bucket(s3)

    if target_date is None:
        partition = today_partition()
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        start_of_today, end_of_today = _get_today_date_range()
    else:
        target_dt = target_date.replace(tzinfo=timezone.utc)
        partition = target_dt.strftime("%Y/%m/%d/")
        run_id = target_dt.strftime("%Y%m%d_%H%M%S")
        start_of_today, end_of_today = _get_today_date_range(target_date)

    counts = {}

    try:
        for name, collection_name in MONGO_COLLECTIONS.items():
            # Filter for documents created today only
            query = {"created_at": {"$gte": start_of_today, "$lt": end_of_today}}
            docs = list(db[collection_name].find(query))
            docs = [_serialize_doc(d) for d in docs]

            if docs:
                key = f"{name}/{partition}{run_id}.json"
                body = json.dumps(docs, indent=2, default=str)
                s3.put_object(
                    Bucket=MINIO_BUCKET,
                    Key=key,
                    Body=body.encode("utf-8"),
                    ContentType="application/json",
                )
                print(f"  ✓ Wrote {len(docs)} {name} to MinIO → {key}")

            counts[name] = len(docs)
    finally:
        client.close()

    return counts


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target_date = datetime.fromisoformat(sys.argv[1])
        extract_to_minio(target_date)
    else:
        extract_to_minio()
