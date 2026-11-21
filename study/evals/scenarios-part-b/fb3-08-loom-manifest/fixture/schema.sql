CREATE TABLE loom_manifest (
    id INTEGER PRIMARY KEY,
    bolt TEXT NOT NULL,
    retired_at TEXT
);
INSERT INTO loom_manifest (id, bolt, retired_at) VALUES (1, 'warp-a', NULL);
