CREATE SCHEMA IF NOT EXISTS monitoring;

CREATE TABLE IF NOT EXISTS monitoring.batch_log (
    id            SERIAL PRIMARY KEY,
    run_id        VARCHAR(50)  NOT NULL,
    table_name    VARCHAR(100) NOT NULL,
    batch_date    DATE         NOT NULL DEFAULT CURRENT_DATE,
    source_rows   INTEGER      NOT NULL,
    loaded_rows   INTEGER      NOT NULL,
    variance      INTEGER      NOT NULL,
    load_time     TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS monitoring.data_quality_log (
    id            SERIAL PRIMARY KEY,
    run_id        VARCHAR(50)  NOT NULL,
    check_name    VARCHAR(100) NOT NULL,
    failed_count  INTEGER      NOT NULL,
    detail        TEXT,
    logged_at     TIMESTAMP    NOT NULL DEFAULT NOW()
);
