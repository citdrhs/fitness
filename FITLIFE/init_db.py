import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, "fitlife.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('Student','Coach','Admin')),
  status TEXT NOT NULL CHECK(status IN ('Active','Pending')),
  team_id INTEGER,
  age INTEGER,
  goal TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS workouts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  date TEXT NOT NULL,                 -- ISO date: YYYY-MM-DD
  workout_type TEXT NOT NULL,
  duration_min INTEGER NOT NULL DEFAULT 0,
  calories INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_workouts_user_date ON workouts(user_id, date);
"""

DEFAULT_TEAMS = ["Basketball", "Football", "Soccer", "Track", "Baseball", "Swimming", "Tennis", "Volleyball"]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)

    # seed teams
    cur = conn.execute("SELECT COUNT(*) FROM teams;")
    (count,) = cur.fetchone()
    if count == 0:
        conn.executemany("INSERT INTO teams (name) VALUES (?);", [(t,) for t in DEFAULT_TEAMS])

    conn.commit()
    conn.close()
    print("✅ Database initialized at", DB_PATH)

if __name__ == "__main__":
    init_db()
