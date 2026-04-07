# Data Dictionary — Staging Tables

## staging.customers_clean

| Column | Type | Meaning | Rule |
|--------|------|---------|------|
| customer_id | varchar(50) | Unique customer identifier | non-null, primary key |
| name | varchar(200) | Customer full name | non-null, title case |
| email | varchar(200) | Customer email address | lowercase, default "unknown@example.com" |
| phone | varchar(50) | Customer phone number | default "N/A" |
| city | varchar(100) | Customer city | title case, default "Unknown" |
| batch_id | varchar(50) | Source batch identifier | non-null (source metadata) |
| created_at | timestamp | Record creation time | non-null |

## staging.products_clean

| Column | Type | Meaning | Rule |
|--------|------|---------|------|
| product_id | varchar(50) | Unique product identifier | non-null, primary key |
| product_name | varchar(200) | Product display name | non-null, title case |
| category | varchar(100) | Product category | title case, default "Uncategorized" |
| price | numeric(12,2) | Product unit price | non-negative, default 0 |
| batch_id | varchar(50) | Source batch identifier | non-null (source metadata) |
| created_at | timestamp | Record creation time | non-null |

## staging.orders_clean

| Column | Type | Meaning | Rule |
|--------|------|---------|------|
| order_id | varchar(50) | Unique order identifier | non-null, primary key |
| customer_id | varchar(50) | Customer who placed order | non-null |
| product_id | varchar(50) | Product ordered | non-null |
| region | varchar(100) | Standardized business region | title case |
| amount | numeric(12,2) | Transaction amount | positive |
| payment_status | varchar(20) | Payment outcome | controlled values: paid, failed, pending |
| batch_id | varchar(50) | Source batch identifier | non-null (source metadata) |
| created_at | timestamp | Record creation time | non-null |

## monitoring.batch_log

| Column | Type | Meaning | Rule |
|--------|------|---------|------|
| id | serial | Auto-incrementing primary key | system-generated |
| run_id | varchar(50) | Pipeline run timestamp | format: YYYYMMDD_HHMMSS |
| table_name | varchar(100) | Raw table name | matches raw.* table |
| batch_date | date | Date of pipeline run | defaults to current date |
| source_rows | integer | Rows extracted from MongoDB | non-negative |
| loaded_rows | integer | Rows loaded into raw table | non-negative |
| variance | integer | source_rows - loaded_rows | 0 = healthy |
| load_time | timestamp | When the load completed | system-generated |
