CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL,
  legacy_code TEXT
);

INSERT INTO customers (id, email, legacy_code) VALUES
  (1, 'ana@example.org', 'A'),
  (2, 'lee@example.org', 'C'),
  (3, 'sam@example.org', 'B');
