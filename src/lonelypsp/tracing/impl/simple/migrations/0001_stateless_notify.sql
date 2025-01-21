BEGIN IMMEDIATE TRANSACTION;

CREATE TABLE stateless_notifies (
    id INTEGER PRIMARY KEY,
    uid BLOB UNIQUE NOT NULL,
    topic BLOB NULL,
    length INTEGER NULL,
    created_at REAL NOT NULL,
    finished_at REAL NULL
);

CREATE TABLE stateless_notify_timings (
    id INTEGER PRIMARY KEY,
    notify_id INTEGER NOT NULL REFERENCES stateless_notifies(id) ON DELETE CASCADE ON UPDATE RESTRICT,
    ord INTEGER NOT NULL,
    name TEXT NOT NULL,
    extra TEXT NULL,
    occurred_at REAL NOT NULL,
    raw_occurred_at REAL NOT NULL
);

/* Foreign key */
CREATE INDEX stateless_notify_timings_notify_id_name_idx ON stateless_notify_timings(notify_id, name);

/* Search */
CREATE INDEX stateless_notify_timings_name_idx ON stateless_notify_timings(name);

COMMIT TRANSACTION;