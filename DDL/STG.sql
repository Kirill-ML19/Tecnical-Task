CREATE SCHEMA IF NOT EXISTS stg;

CREATE TABLE IF NOT EXISTS stg.post_stg(
    load_dttm TIMESTAMP NOT NULL,
    source_system VARCHAR(100) NOT NULL,
    post_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    title TEXT,
    body TEXT,
    record_hash VARCHAR(64) NOT NULL
);