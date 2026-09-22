from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"


def connect_db():
    return sqlite3.connect("database.db")


# 🔐 LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()

        user = cur.execute("""
            SELECT * FROM users 
            WHERE username=? AND password=?
        """, (username, password)).fetchone()

        conn.close()

        if user:
            session["role"] = user[3]

            if user[3] == "ADMIN":
                return redirect("/admin")
            elif user[3] == "USER":
                return redirect("/user")
            else:
                return redirect("/driver/1")

        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


# 🚪 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# 🏠 HOME → redirect to login
@app.route("/")
def home():
    return redirect("/login")


# 🧑‍💼 ADMIN DASHBOARD
@app.route("/admin")
def admin():
    conn = connect_db()
    cur = conn.cursor()

    search = request.args.get("search", "")
    sort = request.args.get("sort")

    # 🔄 SORT LOGIC
    order_by = "bins.id DESC"  # default

    if sort == "asc":
        order_by = "bins.fill_level ASC"
    elif sort == "desc":
        order_by = "bins.fill_level DESC"

    # 🧠 BASE QUERY
    query = """
        SELECT 
            bins.id,
            bins.location,
            bins.fill_level,
            bins.status,
            GROUP_CONCAT(DISTINCT drivers.name) as drivers
        FROM bins
        LEFT JOIN collections ON bins.id = collections.bin_id
        LEFT JOIN drivers ON drivers.id = collections.driver_id
    """

    params = []

    # 🔍 SEARCH
    if search:
        query += " WHERE bins.location LIKE ?"
        params.append(f"%{search}%")

    # 🧩 FINAL QUERY
    query += f"""
        GROUP BY bins.id
        ORDER BY {order_by}
        LIMIT 100
    """

    bins = cur.execute(query, tuple(params)).fetchall()

    # 📊 STATS
    total = cur.execute("SELECT COUNT(*) FROM bins").fetchone()[0]
    full = cur.execute("SELECT COUNT(*) FROM bins WHERE status='FULL'").fetchone()[0]
    half = cur.execute("SELECT COUNT(*) FROM bins WHERE status='HALF'").fetchone()[0]

    drivers = cur.execute("SELECT * FROM drivers").fetchall()

    conn.close()

    return render_template(
        "admin.html",
        bins=bins,
        total=total,
        full=full,
        half=half,
        drivers=drivers
    )


# 👤 USER PANEL
@app.route("/user")
def user():
    conn = connect_db()
    cur = conn.cursor()

    search = request.args.get("search", "")

    if search:
        bins = cur.execute("""
            SELECT * FROM bins
            WHERE location LIKE ?
            ORDER BY id DESC
            LIMIT 100
        """, (f"%{search}%",)).fetchall()
    else:
        bins = cur.execute("""
            SELECT * FROM bins
            ORDER BY id DESC
            LIMIT 100
        """).fetchall()

    conn.close()

    return render_template("user.html", bins=bins)


# 🚛 DRIVER PANEL
@app.route("/driver/<int:driver_id>")
def driver(driver_id):

    conn = connect_db()
    cur = conn.cursor()

    search = request.args.get("search", "")
    sort = request.args.get("sort")  # only "status"

    query = """
        SELECT 
            collections.id, 
            bins.location, 
            bins.fill_level,
            bins.status,
            collections.status
        FROM collections
        JOIN bins ON bins.id = collections.bin_id
        WHERE driver_id=?
    """

    params = [driver_id]

    if search:
        query += " AND bins.location LIKE ?"
        params.append(f"%{search}%")

    # sorting
    if sort == "status":
        query += " ORDER BY collections.status='DONE', collections.id DESC"
    else:
        query += " ORDER BY collections.id DESC"

    tasks = cur.execute(query, tuple(params)).fetchall()

    # summary
    pending = cur.execute("""
        SELECT COUNT(*) FROM collections 
        WHERE driver_id=? AND status='PENDING'
    """, (driver_id,)).fetchone()[0]

    done = cur.execute("""
        SELECT COUNT(*) FROM collections 
        WHERE driver_id=? AND status='DONE'
    """, (driver_id,)).fetchone()[0]

    conn.close()

    return render_template(
        "driver.html",
        tasks=tasks,
        pending=pending,
        done=done,
        driver_id=driver_id
    )


# ➕ ADD BIN
@app.route("/add_bin", methods=["POST"])
def add_bin():
    location = request.form["location"]

    conn = connect_db()
    cur = conn.cursor()

    # Step 1: insert normally
    cur.execute("""
        INSERT INTO bins (location, fill_level, status, last_collected)
        VALUES (?, ?, ?, ?)
    """, (location, 0, "EMPTY", None))

    # Step 2: get auto-generated bin ID
    bin_id = cur.lastrowid

    # Step 3: update location with bin ID prefix
    new_location = f"Bin #{bin_id} - {location}"

    cur.execute("""
        UPDATE bins SET location=? WHERE id=?
    """, (new_location, bin_id))

    conn.commit()
    conn.close()

    return redirect(request.referrer)


# 🔄 UPDATE BIN
@app.route("/update_bin/<int:id>", methods=["POST"])
def update_bin(id):
    fill = int(request.form["fill_level"])

    status = "EMPTY"
    if fill > 70:
        status = "FULL"
    elif fill > 30:
        status = "HALF"

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE bins SET fill_level=?, status=? WHERE id=?",
        (fill, status, id)
    )
    conn.commit()
    conn.close()

    return redirect(request.referrer)


# 🚛 ASSIGN DRIVER
@app.route("/assign/<int:bin_id>", methods=["POST"])
def assign(bin_id):
    driver_id = request.form["driver_id"]

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO collections (bin_id, driver_id) VALUES (?, ?)",
        (bin_id, driver_id)
    )
    conn.commit()
    conn.close()

    return redirect("/admin")


# ✅ MARK AS COLLECTED
@app.route("/collect/<int:id>")
def collect(id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE collections SET status='DONE', collected_at=? WHERE id=?",
        (datetime.now(), id)
    )

    cur.execute("""
        UPDATE bins 
        SET fill_level=0, status='EMPTY', last_collected=? 
        WHERE id=(SELECT bin_id FROM collections WHERE id=?)
    """, (datetime.now(), id))

    conn.commit()
    conn.close()

    return redirect(request.referrer)


# ▶️ RUN
if __name__ == "__main__":
    app.run(debug=True)