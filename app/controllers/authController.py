"""
Auth controller — register, login, logout.
Includes account lockout after repeated failed attempts.
"""

from datetime import datetime, timedelta

from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from app.database import get_connection


# ------------------------- LOCKOUT CONFIG ---------------------------
MAX_FAILED_ATTEMPTS = 5     # After this many, account locks
LOCKOUT_DURATION_MIN = 15   # Lock duration in minutes


# ==========================================================================
# REGISTER
# ==========================================================================
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip()

        # --- validation ---
        errors = []
        if len(name) < 2:
            errors.append("Name must be at least 2 characters.")
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if role not in ("client", "provider"):
            errors.append("Please choose a role.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "auth/auth.html",
                mode="register",
                name=name,
                email=email,
                role=role,
            )

        # --- Check email uniqueness ---
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash("That email is already registered. Try logging in.", "danger")
                    return render_template(
                        "auth/auth.html",
                        mode="register",
                        name=name,
                        email=email,
                        role=role,
                    )

                # --- Create the user ---
                hashed = generate_password_hash(password)
                cursor.execute(
                    """INSERT INTO users (name, email, password, role)
                       VALUES (%s, %s, %s, %s)""",
                    (name, email, hashed, role),
                )
                conn.commit()
        finally:
            conn.close()

        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/auth.html", mode="register")


# ==========================================================================
# LOGIN — with account lockout
# ==========================================================================
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT id, name, email, password, role,
                              failed_attempts, locked_until
                       FROM users WHERE email = %s""",
                    (email,),
                )
                user = cursor.fetchone()

                # --- Step 1: enumeration protection ---
                # If user doesn't exist, return the same generic message
                # (don't tell attackers which emails are valid)
                if user is None:
                    flash("Invalid email or password.", "danger")
                    return render_template(
                        "auth/auth.html", mode="login", email=email
                    )

                # --- Step 2: is the account currently locked? ---
                now = datetime.utcnow()
                if user["locked_until"] and user["locked_until"] > now:
                    remaining = user["locked_until"] - now
                    minutes = int(remaining.total_seconds() // 60) + 1
                    flash(
                        f"This account is locked due to too many failed attempts. "
                        f"Try again in {minutes} minute{'s' if minutes != 1 else ''}.",
                        "danger",
                    )
                    return render_template(
                        "auth/auth.html", mode="login", email=email
                    )

                # --- Step 3: verify password ---
                if not check_password_hash(user["password"], password):
                    # Wrong password — increment failed attempts
                    new_attempts = (user["failed_attempts"] or 0) + 1

                    if new_attempts >= MAX_FAILED_ATTEMPTS:
                        # Lock the account
                        lock_until = now + timedelta(minutes=LOCKOUT_DURATION_MIN)
                        cursor.execute(
                            """UPDATE users
                               SET failed_attempts = %s, locked_until = %s
                               WHERE id = %s""",
                            (new_attempts, lock_until, user["id"]),
                        )
                        conn.commit()
                        flash(
                            f"Account locked for {LOCKOUT_DURATION_MIN} minutes "
                            f"due to {MAX_FAILED_ATTEMPTS} failed login attempts.",
                            "danger",
                        )
                    else:
                        # Just increment and warn
                        cursor.execute(
                            "UPDATE users SET failed_attempts = %s WHERE id = %s",
                            (new_attempts, user["id"]),
                        )
                        conn.commit()
                        remaining_attempts = MAX_FAILED_ATTEMPTS - new_attempts
                        flash(
                            f"Invalid email or password. "
                            f"{remaining_attempts} attempt"
                            f"{'s' if remaining_attempts != 1 else ''} left "
                            f"before lockout.",
                            "danger",
                        )
                    return render_template(
                        "auth/auth.html", mode="login", email=email
                    )

                # --- Step 4: successful login — reset counters ---
                cursor.execute(
                    """UPDATE users
                       SET failed_attempts = 0, locked_until = NULL
                       WHERE id = %s""",
                    (user["id"],),
                )
                conn.commit()

                # Set session
                session.clear()
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["user_role"] = user["role"]

                flash(f"Welcome back, {user['name']}.", "success")
                return redirect(url_for("dashboard.dashboard"))
        finally:
            conn.close()

    return render_template("auth/auth.html", mode="login")


# ==========================================================================
# LOGOUT
# ==========================================================================
def logout():
    session.clear()
    flash("You've been logged out.", "success")
    return redirect(url_for("home"))