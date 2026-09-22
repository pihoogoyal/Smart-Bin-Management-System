import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS bins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT,
    fill_level INTEGER DEFAULT 0,
    status TEXT DEFAULT 'EMPTY',
    last_collected DATETIME
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bin_id INTEGER,
    driver_id INTEGER,
    status TEXT DEFAULT 'PENDING',
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    collected_at DATETIME
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

conn.commit()
conn.close()

print("✅ DB Ready")