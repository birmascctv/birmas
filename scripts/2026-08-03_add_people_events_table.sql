-- 2026-08-03: Add people_events table for door in/out counting and
-- store-activity heartbeat (occupancy / foot-traffic feature).
CREATE TABLE IF NOT EXISTS people_events (
    id         SERIAL PRIMARY KEY,
    ts         TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'Asia/Jakarta'),
    camera_id  VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,   -- 'in' | 'out' | 'activity'
    confidence DOUBLE PRECISION DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS ix_people_events_ts ON people_events (ts);
CREATE INDEX IF NOT EXISTS ix_people_events_camera_id ON people_events (camera_id);
CREATE INDEX IF NOT EXISTS ix_people_events_event_type ON people_events (event_type);
