-- Raw is a stateless buffer: source data lands as-is,
-- validation surfaces quality issues as counts, transforms clean into staging.
-- Only pipeline-injected metadata (batch_id, created_at) is constrained.

CREATE SCHEMA IF NOT EXISTS raw;

DROP TABLE IF EXISTS raw.customers_raw CASCADE;
DROP TABLE IF EXISTS raw.products_raw CASCADE;
DROP TABLE IF EXISTS raw.orders_raw CASCADE;

CREATE TABLE raw.customers_raw (
    customer_id   VARCHAR(50),
    name          VARCHAR(200),
    email         VARCHAR(200),
    phone         VARCHAR(50),
    city          VARCHAR(100),
    batch_id      VARCHAR(50)  NOT NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE raw.products_raw (
    product_id    VARCHAR(50),
    product_name  VARCHAR(200),
    category      VARCHAR(100),
    price         NUMERIC(12,2),
    batch_id      VARCHAR(50)  NOT NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE raw.orders_raw (
    order_id       VARCHAR(50),
    customer_id    VARCHAR(50),
    product_id     VARCHAR(50),
    region         VARCHAR(100),
    amount         NUMERIC(12,2),
    payment_status VARCHAR(20),
    batch_id       VARCHAR(50)  NOT NULL,
    created_at     TIMESTAMP    NOT NULL DEFAULT NOW()
);
