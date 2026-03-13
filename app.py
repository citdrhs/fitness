from __future__ import annotations

import os
import sqlite3
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional, Dict

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, g
)
from werkzeug.security import generate_password_hash, check_password_hash

# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, "fitlife.db")

app = Flask(__name__)
# IMPORTANT: In real deployments use an env var. For class projects, this is ok.
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.permanent_session_lifetime = timedelta(days=7)

# -----------------------------------------------------------------------------
# Database helpers
# -----------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """
    Get a per-request sqlite connection. Uses Row factory so rows behave like dicts.
    """
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db

@app.teardown_appcontext
def close_db(_: Optional[BaseException]) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

def query_one(sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
    cur = get_db().execute(sql, params)
    row = cur.fetchone()
    cur.close()
    return row

def query_all(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    cur = get_db().execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows

def execute(sql: str, params: tuple = ()) -> int:
    cur = get_db().execute(sql, params)
    get_db().commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id

# -----------------------------------------------------------------------------
# Security helpers (simple CSRF for POST)
# -----------------------------------------------------------------------------

def ensure_csrf() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(24)
    return session["csrf_token"]

@app.context_processor
def inject_globals() -> Dict[str, Any]:
    # available in every template
    return {"csrf_token": ensure_csrf(), "current_user": current_user()}

def csrf_protect() -> None:
    if request.method == "POST":
        token = session.get("csrf_token")
        form_token = request.form.get("csrf_token")
        if not token or not form_token or token != form_token:
            abort(400, description="CSRF token missing/invalid")

app.before_request(csrf_protect)

# -----------------------------------------------------------------------------
# Auth helpers
# -----------------------------------------------------------------------------

def current_user() -> Optional[sqlite3.Row]:
    uid = session.get("user_id")
    if not uid:
        return None
    return query_one("SELECT * FROM users WHERE id = ?;", (uid,))

def login_required(view: Callable) -> Callable:
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def role_required(*roles: str) -> Callable:
    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Please log in first.", "warning")
                return redirect(url_for("login", next=request.path))
            if user["role"] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator

def set_login(user_id: int, remember: bool = False) -> None:
    session.clear()
    session["user_id"] = user_id
    session["csrf_token"] = secrets.token_urlsafe(24)
    session.permanent = bool(remember)

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        if not identifier or not password:
            flash("Please enter your username/email and password.", "error")
            return render_template("login.html")

        user = query_one(
            "SELECT * FROM users WHERE username = ? OR email = ?;",
            (identifier, identifier),
        )

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Username/email and password don't match.", "error")
            return render_template("login.html")

        if user["status"] == "Pending":
            flash("Your account is awaiting admin approval.", "warning")
            return render_template("login.html")

        set_login(int(user["id"]), remember=remember)

        nxt = request.args.get("next")
        return redirect(nxt or url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    teams = query_all("SELECT id, name FROM teams ORDER BY name;")

    if request.method == "POST":
        role = request.form.get("role", "")
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        team_id = request.form.get("team_id", "").strip() or None

        if role not in {"Student", "Coach"}:
            flash("Please select Student or Coach.", "error")
            return render_template("signup.html", teams=teams)

        if len(username) < 3 or len(username) > 24:
            flash("Username must be 3–24 characters.", "error")
            return render_template("signup.html", teams=teams)

        if "@" not in email or "." not in email:
            flash("Please enter a valid email.", "error")
            return render_template("signup.html", teams=teams)

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("signup.html", teams=teams)

        # uniqueness checks
        if query_one("SELECT 1 FROM users WHERE username = ?;", (username,)):
            flash("That username is already taken.", "error")
            return render_template("signup.html", teams=teams)

        if query_one("SELECT 1 FROM users WHERE email = ?;", (email,)):
            flash("That email is already in use.", "error")
            return render_template("signup.html", teams=teams)

        status = "Pending" if role == "Coach" else "Active"

        user_id = execute(
            """
            INSERT INTO users (username, email, password_hash, role, status, team_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                username,
                email,
                generate_password_hash(password),
                role,
                status,
                team_id,
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )

        # Students can log in immediately; coaches wait for approval
        if status == "Active":
            set_login(user_id, remember=True)
            flash("Welcome! Your account was created.", "success")
            return redirect(url_for("dashboard"))

        flash("Account created! Awaiting admin approval for Coach access.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html", teams=teams)

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    assert user is not None

    if user["role"] == "Student":
        stats = query_one(
            """
            SELECT
              COUNT(*) AS workout_count,
              COALESCE(SUM(calories), 0) AS calories_total,
              COALESCE(SUM(duration_min), 0) AS minutes_total
            FROM workouts
            WHERE user_id = ?;
            """,
            (user["id"],),
        )
        recent = query_all(
            """
            SELECT id, date, workout_type, duration_min, calories
            FROM workouts
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
            LIMIT 8;
            """,
            (user["id"],),
        )
        return render_template("dashboard_student.html", user=user, stats=stats, recent=recent)

    if user["role"] == "Coach":
        # show all students on same team
        athletes = query_all(
            """
            SELECT u.id, u.username, u.email,
                   COALESCE(COUNT(w.id), 0) AS workout_count,
                   COALESCE(SUM(w.calories), 0) AS calories_total
            FROM users u
            LEFT JOIN workouts w ON w.user_id = u.id
            WHERE u.role = 'Student' AND u.team_id = ?
            GROUP BY u.id
            ORDER BY u.username;
            """,
            (user["team_id"],),
        )
        return render_template("dashboard_coach.html", user=user, athletes=athletes)

    # Admin view
    pending = query_all("SELECT id, username, email, created_at FROM users WHERE status = 'Pending' ORDER BY created_at;")
    return render_template("dashboard_admin.html", user=user, pending=pending)

@app.route("/workouts/new", methods=["GET", "POST"])
@login_required
@role_required("Student")
def workout_new():
    user = current_user()
    assert user is not None

    if request.method == "POST":
        workout_type = request.form.get("workout_type", "").strip()
        date = request.form.get("date", "").strip()
        duration = request.form.get("duration_min", "").strip()
        calories = request.form.get("calories", "").strip()

        # Validate
        if not workout_type:
            flash("Workout type is required.", "error")
            return render_template("workout_new.html")
        try:
            duration_i = max(0, int(duration))
            calories_i = max(0, int(calories))
        except ValueError:
            flash("Duration and calories must be whole numbers.", "error")
            return render_template("workout_new.html")

        # allow empty date => today
        if not date:
            date = datetime.utcnow().date().isoformat()

        execute(
            """
            INSERT INTO workouts (user_id, date, workout_type, duration_min, calories)
            VALUES (?, ?, ?, ?, ?);
            """,
            (user["id"], date, workout_type, duration_i, calories_i),
        )

        flash("Workout logged!", "success")
        return redirect(url_for("dashboard"))

    return render_template("workout_new.html")

@app.route("/athlete/<int:athlete_id>")
@login_required
@role_required("Coach")
def athlete_detail(athlete_id: int):
    coach = current_user()
    assert coach is not None

    athlete = query_one(
        "SELECT * FROM users WHERE id = ? AND role = 'Student' AND team_id = ?;",
        (athlete_id, coach["team_id"]),
    )
    if not athlete:
        abort(404)

    stats = query_one(
        """
        SELECT COUNT(*) AS workout_count,
               COALESCE(SUM(calories), 0) AS calories_total,
               COALESCE(SUM(duration_min), 0) AS minutes_total
        FROM workouts
        WHERE user_id = ?;
        """,
        (athlete_id,),
    )
    recent = query_all(
        """
        SELECT id, date, workout_type, duration_min, calories
        FROM workouts
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        LIMIT 15;
        """,
        (athlete_id,),
    )
    return render_template("athlete_detail.html", coach=coach, athlete=athlete, stats=stats, recent=recent)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    assert user is not None

    if request.method == "POST":
        age = request.form.get("age", "").strip()
        goal = request.form.get("goal", "").strip()

        age_val = None
        if age:
            try:
                age_val = int(age)
                if age_val < 0 or age_val > 120:
                    raise ValueError
            except ValueError:
                flash("Please enter a valid age.", "error")
                return render_template("profile.html", user=user)

        execute("UPDATE users SET age = ?, goal = ? WHERE id = ?;", (age_val, goal, user["id"]))
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))

    # refresh
    user = current_user()
    return render_template("profile.html", user=user)

@app.route("/requests")
@login_required
@role_required("Admin")
def requests():
    pending = query_all(
        "SELECT id, username, email, role, created_at FROM users WHERE status = 'Pending' ORDER BY created_at;"
    )
    return render_template("requests.html", pending=pending)

@app.route("/requests/approve", methods=["POST"])
@login_required
@role_required("Admin")
def approve_request():
    user_id = request.form.get("user_id", "").strip()
    try:
        uid = int(user_id)
    except ValueError:
        abort(400)

    execute("UPDATE users SET status = 'Active' WHERE id = ? AND status = 'Pending';", (uid,))
    flash("Account approved.", "success")
    return redirect(url_for("requests"))

@app.route("/requests/deny", methods=["POST"])
@login_required
@role_required("Admin")
def deny_request():
    user_id = request.form.get("user_id", "").strip()
    try:
        uid = int(user_id)
    except ValueError:
        abort(400)

    execute("DELETE FROM users WHERE id = ? AND status = 'Pending';", (uid,))
    flash("Request denied and account deleted.", "success")
    return redirect(url_for("requests"))

# -----------------------------------------------------------------------------
# Dev helper: create an admin if none exists
# -----------------------------------------------------------------------------

@app.route("/dev/create_admin")
def dev_create_admin():
    """
    For class/demo use only.
    Creates: admin / admin12345 (change after first login)
    """
    if query_one("SELECT 1 FROM users WHERE role='Admin';"):
        flash("Admin already exists.", "info")
        return redirect(url_for("login"))

    admin_id = execute(
        """
        INSERT INTO users (username, email, password_hash, role, status, team_id, created_at)
        VALUES (?, ?, ?, 'Admin', 'Active', NULL, ?);
        """,
        ("admin", "admin@example.com", generate_password_hash("admin12345"), datetime.utcnow().isoformat(timespec="seconds")),
    )
    flash("Admin created: username=admin password=admin12345", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
