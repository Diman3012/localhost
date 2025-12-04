-- Recommended indexes to improve query performance (apply on your MySQL server)
-- Run these once in your database (adjust names/schema if needed)

CREATE INDEX idx_arrivals_warehouse_arrived ON arrivals (warehouse_id, arrived_at DESC);
CREATE INDEX idx_arrivals_warehouse_status ON arrivals (warehouse_id, status_id);
CREATE INDEX idx_packages_arrival ON packages (arrival_id);
CREATE INDEX idx_packages_blocks ON packages (arrival_id, blocks_count);
CREATE INDEX idx_eventlog_arrival_time ON event_log (arrival_id, event_time DESC);
CREATE INDEX idx_statuses_name ON statuses (name(50)); -- prefix index for long names if necessary

-- These indexes will help the queries that filter by warehouse_id, status_id and order by arrived_at/event_time.
