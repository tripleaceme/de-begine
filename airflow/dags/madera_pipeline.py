"""
Mandera Analytics – Batch Pipeline DAG

Data generation is handled separately by GitHub Actions (8 AM & 4 PM WAT).
This DAG picks up whatever landed in MongoDB and processes it through:

  extract to MinIO → load raw tables → log monitoring counts →
  validate data quality → transform to staging → truncate raw

Schedule:
  - 08:30 AM WAT (07:30 UTC)
  - 04:30 PM WAT (15:30 UTC)
"""

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/airflow/dags")  # Ensure DAG can import from the project root

from extraction.extract_mongo_to_minio import extract_to_minio
from extraction.extract_mongo_to_postgres import extract_to_postgres
from validation.validate_batch_counts import log_counts
from validation.validate_data_quality import validate
from transformation.transform_customers import transform as transform_customers
from transformation.transform_products import transform as transform_products
from transformation.transform_orders import transform as transform_orders
from maintenance.truncate_raw_tables import truncate


# ── Failure callback ──────────────────────────────────────────
def on_task_failure(context):
    task = context["task_instance"]
    print(
        f"✗ TASK FAILED: {task.task_id} | "
        f"DAG: {task.dag_id} | "
        f"Execution: {context['execution_date']} | "
        f"Exception: {context.get('exception', 'N/A')}"
    )


# ── Task callables ────────────────────────────────────────────
def _extract_to_minio(**kwargs):
    counts = extract_to_minio()
    kwargs["ti"].xcom_push(key="minio_counts", value=counts)


def _extract_to_postgres(**kwargs):
    counts = extract_to_postgres()
    kwargs["ti"].xcom_push(key="pg_counts", value=counts)


def _log_monitoring(**kwargs):
    counts = kwargs["ti"].xcom_pull(task_ids="extract_to_postgres", key="pg_counts")
    log_counts(counts)


def _validate_quality(**kwargs):
    validate()


def _transform_customers(**kwargs):
    from sqlalchemy import create_engine
    from config.postgres_settings import POSTGRES_URL
    transform_customers(create_engine(POSTGRES_URL))


def _transform_products(**kwargs):
    from sqlalchemy import create_engine
    from config.postgres_settings import POSTGRES_URL
    transform_products(create_engine(POSTGRES_URL))


def _transform_orders(**kwargs):
    from sqlalchemy import create_engine
    from config.postgres_settings import POSTGRES_URL
    transform_orders(create_engine(POSTGRES_URL))


def _truncate_raw(**kwargs):
    truncate()


# ── DAG definition ────────────────────────────────────────────
default_args = {
    "owner": "begine_fusion_analytics",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": on_task_failure,
    "sla": timedelta(hours=1),
}

with DAG(
    dag_id="begine_fusion_batch_pipeline",
    default_args=default_args,
    description="Analytics pipeline: MongoDB → MinIO + Postgres raw → staging",
    schedule_interval="30 7,15 * * *",
    start_date=datetime(2026, 3, 23),
    catchup=False,
    tags=["begine fusion", "batch", "analytics"],
    max_active_runs=1,
) as dag:

    extract_minio = PythonOperator(
        task_id="extract_to_minio",
        python_callable=_extract_to_minio,
    )

    extract_postgres = PythonOperator(
        task_id="extract_to_postgres",
        python_callable=_extract_to_postgres,
    )

    log_monitoring = PythonOperator(
        task_id="log_monitoring",
        python_callable=_log_monitoring,
    )

    validate_quality = PythonOperator(
        task_id="validate_data_quality",
        python_callable=_validate_quality,
    )

    transform_cust = PythonOperator(
        task_id="transform_customers",
        python_callable=_transform_customers,
    )

    transform_prod = PythonOperator(
        task_id="transform_products",
        python_callable=_transform_products,
    )

    transform_ord = PythonOperator(
        task_id="transform_orders",
        python_callable=_transform_orders,
    )

    truncate_raw = PythonOperator(
        task_id="truncate_raw_tables",
        python_callable=_truncate_raw,
    )

    # ── Task dependencies ─────────────────────────────────────
    # Extraction: MinIO and Postgres run in parallel
    [extract_minio, extract_postgres] >> log_monitoring >> validate_quality

    # Transforms run in parallel after validation passes
    validate_quality >> [transform_cust, transform_prod, transform_ord] >> truncate_raw
