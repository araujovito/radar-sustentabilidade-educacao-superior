CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS raw.source_registry (
    source_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name TEXT NOT NULL,
    reference_year SMALLINT NOT NULL,
    source_url TEXT NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_name TEXT NOT NULL,
    file_size_bytes BIGINT,
    sha256 CHAR(64),
    UNIQUE (source_name, reference_year, file_name, sha256)
);

CREATE TABLE IF NOT EXISTS raw.ingestion_run (
    ingestion_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES raw.source_registry (source_id),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    rows_read BIGINT,
    rows_loaded BIGINT,
    error_message TEXT
);
