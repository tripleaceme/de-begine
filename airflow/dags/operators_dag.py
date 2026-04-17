from datetime import datetime

from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.email import EmailOperator

with DAG(
    dag_id="operators") as dag:

    ping = SimpleHttpOperator(
        task_id="ping",
        http_conn_id="http_default",
        endpoint="http://example.com/update/",
        method="GET",
    )

    email = EmailOperator(
        task_id="email",
        to="admin@example.com",
        subject="Update complete",
        html_content="The ping task has completed successfully.",
    )

    ping >> email