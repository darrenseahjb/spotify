CREATE TABLE IF NOT EXISTS spotify_history (
    track_id TEXT NOT NULL,
    track_name TEXT NOT NULL,
    artist TEXT NOT NULL,
    album TEXT NOT NULL,
    played_at TIMESTAMPTZ NOT NULL,
    duration_ms INTEGER NOT NULL,
    PRIMARY KEY (track_id, played_at)
);
