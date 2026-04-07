# How to Run the Pipeline

## Prerequisites

- Docker & Docker Compose installed
- MongoDB Atlas cluster (free tier works)
- Python 3.11+

---

## Step 1: Environment Setup

```bash
cd batch-pipeline
cp .env.example .env
```

Edit `.env` — set your MongoDB Atlas connection string:

```
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/mandera_analytics?retryWrites=true&w=majority
MONGO_DB=mandera_analytics
```

For running scripts manually on your local machine (outside Docker),
override the Docker hostnames:

```
POSTGRES_HOST=localhost
MINIO_ENDPOINT=http://localhost:9000
```

---

## Step 2: Start Infrastructure

Start Postgres and MinIO only — no Airflow yet:

```bash
docker compose up -d postgres minio
```

Wait a few seconds, then create schemas and tables:

```bash
docker compose run --rm db-setup
```

Verify tables were created:

```bash
psql -h localhost -U pipeline -d mandera_warehouse -c "\dt raw.*; \dt staging.*; \dt monitoring.*;"
# password: pipeline_secret
```

---

## Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

All commands below must be run from the project root (`batch-pipeline/`).

---

## Step 4: Generate Data → MongoDB Atlas

```bash
python -m generator.data_generator
```

Expected output:

```
  ✓ Inserted 15 customers
  ✓ Inserted 7 products
  ✓ Inserted 3421 orders

✓ Data generation complete.
```

Verify in MongoDB Atlas that the `customers`, `products`, and `orders`
collections have data. Each record has a `batch_id` like `2026_03_23_0700`
automatically stamped based on when the generator ran.

---

## Step 5: Extract → MinIO

```bash
python -m extraction.extract_mongo_to_minio
```

Check MinIO Console at http://localhost:9001
Login: `minioadmin` / `minioadmin123`
Look for: `mandera-raw/customers/2026/03/23/<run_id>.json`

---

## Step 6: Extract → PostgreSQL Raw Tables

```bash
python -m extraction.extract_mongo_to_postgres
```

Verify:

```bash
psql -h localhost -U pipeline -d mandera_warehouse \
  -c "SELECT COUNT(*) FROM raw.orders_raw;"
```

---

## Step 7: Validate Data Quality

```bash
python -m validation.validate_data_quality
```

Expected: `✓ All validation checks passed`

---

## Step 8: Transform Raw → Staging

```bash
python -m transformation.transform_customers
python -m transformation.transform_products
python -m transformation.transform_orders
```

Verify:

```bash
psql -h localhost -U pipeline -d mandera_warehouse \
  -c "SELECT COUNT(*) FROM staging.orders_clean;"
```

---

## Step 9: Truncate Raw Tables

```bash
python -m maintenance.truncate_raw_tables
```

Verify raw is now empty:

```bash
psql -h localhost -U pipeline -d mandera_warehouse \
  -c "SELECT COUNT(*) FROM raw.orders_raw;"
```

---

## Step 10: Run with Airflow

Once everything works manually, bring up the full stack:

```bash
docker compose up -d
```

| Service        | URL                    | Credentials               |
|----------------|------------------------|---------------------------|
| Airflow UI     | http://localhost:8080   | admin / admin             |
| MinIO Console  | http://localhost:9001   | minioadmin / minioadmin123|
| PostgreSQL     | localhost:5432          | pipeline / pipeline_secret|

In the Airflow UI:

1. Find `mandera_batch_pipeline` in the DAGs list
2. Toggle it **ON**
3. Click the play button to trigger a manual run
4. Watch the task graph — extractions run in parallel, then monitoring → validation → transforms in parallel → truncate

---

## Teardown

```bash
# stop everything
docker compose down

# stop and delete all data (volumes)
docker compose down -v
```
