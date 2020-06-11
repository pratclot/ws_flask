CREATE TABLE roles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

INSERT INTO roles (id, name) VALUES
    ("0", "nothing"),
    ("1", "read"),
    ("2", "write");

CREATE TABLE user (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  profile_pic TEXT NOT NULL,
  role TEXT DEFAULT "0",
  FOREIGN KEY(role) REFERENCES roles(id)
);
