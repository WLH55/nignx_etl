CREATE DATABASE IF NOT EXISTS demo;

CREATE TABLE IF NOT EXISTS demo.analytics_log
(
    event_time DateTime,
    event_date Date DEFAULT toDate(event_time),
    remote_ip String,
    request_uri String,
    status UInt16
)
ENGINE = MergeTree()
PARTITION BY event_date
ORDER BY (event_time, request_uri);

