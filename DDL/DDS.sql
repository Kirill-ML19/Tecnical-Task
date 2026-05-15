CREATE SCHEMA IF NOT EXISTS dds;

CREATE TABLE IF NOT EXISTS dds.hub_user ( 
    hub_user_hash_key VARCHAR(64) PRIMARY KEY, 
    user_id BIGINT NOT NULL, 
    load_dttm TIMESTAMP NOT NULL, 
    record_source VARCHAR(100) NOT NULL 
);

CREATE TABLE IF NOT EXISTS dds.hub_post ( 
    hub_post_hash_key VARCHAR(64) PRIMARY KEY, 
    post_id BIGINT NOT NULL,
    load_dttm TIMESTAMP NOT NULL, 
    record_source VARCHAR(100) NOT NULL 
);

CREATE TABLE IF NOT EXISTS dds.link_user_post ( 
    link_user_post_hash_key VARCHAR(64) PRIMARY KEY,
    hub_user_hash_key VARCHAR(64) NOT NULL,
    hub_post_hash_key VARCHAR(64) NOT NULL,
    load_dttm TIMESTAMP NOT NULL,
    record_source VARCHAR(100) NOT NULL,

    CONSTRAINT fk_link_user_post_hub_user
        FOREIGN KEY (hub_user_hash_key)
        REFERENCES dds.hub_user(hub_user_hash_key),
    
    CONSTRAINT fk_link_user_post_hub_post
        FOREIGN KEY (hub_post_hash_key)
        REFERENCES dds.hub_post(hub_post_hash_key)
);

CREATE TABLE IF NOT EXISTS dds.sat_post_details (
    hub_post_hash_key VARCHAR(64) NOT NULL,
    title TEXT,
    body TEXT,
    hash_diff VARCHAR(64) NOT NULL,
    load_dttm TIMESTAMP NOT NULL,
    record_source VARCHAR(100) NOT NULL,

    PRIMARY KEY (hub_post_hash_key, hash_diff),

    CONSTRAINT fk_sat_post_details_hub_post 
        FOREIGN KEY (hub_post_hash_key)
        REFERENCES dds.hub_post(hub_post_hash_key)
);