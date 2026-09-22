import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# ---- USERS ----
if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
    users = [
        ("admin", "admin123", "ADMIN"),
        ("driver1", "123", "DRIVER"),
        ("driver2", "123", "DRIVER"),
        ("driver3", "123", "DRIVER"),
        ("user", "123", "USER")
    ]
    for u in users:
        cur.execute("INSERT INTO users VALUES (NULL, ?, ?, ?)", u)

# ---- DRIVERS ----
if cur.execute("SELECT COUNT(*) FROM drivers").fetchone()[0] == 0:
    for i in range(1, 21):
        cur.execute("INSERT INTO drivers (name) VALUES (?)", (f"Driver {i}",))

# ---- REALISTIC LOCATIONS ----
areas = [
    "Connaught Place", "Karol Bagh", "Lajpat Nagar", "Saket",
    "Dwarka Sector 10", "Rohini Sector 5", "Janakpuri",
    "Rajouri Garden", "Pitampura", "Chandni Chowk",
    "AIIMS Area", "Delhi University", "Noida Sector 62",
    "Gurgaon Cyber City", "Faridabad Market"
]

# ---- BINS ----
if cur.execute("SELECT COUNT(*) FROM bins").fetchone()[0] == 0:
    for i in range(5000):
        fill = random.randint(0, 100)
        status = "EMPTY" if fill <= 30 else "HALF" if fill <= 70 else "FULL"

        location = random.choice(areas)

        # 👇 Add bin number in name
        bin_name = f"Bin #{i+1} - {location}"

        cur.execute("""
        INSERT INTO bins (location, fill_level, status, last_collected)
        VALUES (?, ?, ?, ?)
        """, (
            bin_name,
            fill,
            status,
            datetime.now() - timedelta(days=random.randint(0,5))
        ))

# ---- COLLECTIONS (MAX 3 DRIVERS PER BIN) ----
bin_ids = [row[0] for row in cur.execute("SELECT id FROM bins").fetchall()]

for bin_id in bin_ids:
    assigned_drivers = random.sample(range(1, 21), random.randint(1, 3))

    for driver_id in assigned_drivers:
        status = random.choice(["PENDING", "DONE"])

        cur.execute("""
        INSERT INTO collections (bin_id, driver_id, status, assigned_at)
        VALUES (?, ?, ?, ?)
        """, (
            bin_id,
            driver_id,
            status,
            datetime.now() - timedelta(hours=random.randint(1,48))
        ))

conn.commit()
conn.close()

print("✅ Realistic Data Generated")