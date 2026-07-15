"""
Auth controller — register, login (with 2FA), logout.
Includes account lockout after repeated failed attempts.
"""

from datetime import datetime, timedelta

from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from app.database import get_connection
from app.repository import otp_repo
from app.utils.otp_send import send_otp_via_console


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
        import re
        errors = []
        if len(name) < 2:
            errors.append("Name must be at least 2 characters.")
        if len(name) > 60:
            errors.append("Name must be 60 characters or fewer.")

        # Email: format + length cap
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")
        elif len(email) > 120:
            errors.append("Email must be 120 characters or fewer.")

        # Password: length window + complexity
        if len(password) < 6 or len(password) > 12:
            errors.append("Password must be between 6 and 12 characters.")
        if not re.search(r"[A-Z]", password):
            errors.append("Password must include at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            errors.append("Password must include at least one lowercase letter.")
        if not re.search(r"[0-9]", password):
            errors.append("Password must include at least one number.")
        if not re.search(r"[^A-Za-z0-9]", password):
            errors.append("Password must include at least one symbol.")

        if role not in ("client", "provider"):
            errors.append("Please choose a role.")

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
# LOGIN — with account lockout + 2FA branching
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
                              failed_attempts, locked_until,
                              two_factor_enabled
                       FROM users WHERE email = %s""",
                    (email,),
                )
                user = cursor.fetchone()

                # --- Step 1: enumeration protection ---
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
                    new_attempts = (user["failed_attempts"] or 0) + 1

                    if new_attempts >= MAX_FAILED_ATTEMPTS:
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

                # --- Step 4: password OK — reset failure counters ---
                cursor.execute(
                    """UPDATE users
                       SET failed_attempts = 0, locked_until = NULL
                       WHERE id = %s""",
                    (user["id"],),
                )
                conn.commit()
        finally:
            conn.close()

        # --- Step 5: is 2FA enabled? ---
        if user["two_factor_enabled"]:
            # Don't log them in yet — put user_id in a pending slot
            session.clear()
            session["pending_user_id"] = user["id"]
            session["pending_user_email"] = user["email"]
            session["pending_user_name"] = user["name"]

            # Generate + "send" the OTP
            code = otp_repo.create_for_user(user["id"], purpose="login")
            send_otp_via_console(user["email"], code)

            flash("We've sent you a 6-digit code. Check your terminal (demo mode).",
                  "success")
            return redirect(url_for("auth.verifyOtp"))

        # --- No 2FA: log them in directly ---
        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_role"] = user["role"]

        flash(f"Welcome back, {user['name']}.", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("auth/auth.html", mode="login")


# ==========================================================================
# VERIFY OTP — second step of 2FA login
# ==========================================================================
def verifyOtp():
    """The OTP entry page. Only accessible if login step 1 (password)
    already succeeded — indicated by pending_user_id in session."""
    pending_id = session.get("pending_user_id")
    if not pending_id:
        flash("Please log in first.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        code_attempt = request.form.get("code", "").strip()

        if len(code_attempt) != 6 or not code_attempt.isdigit():
            flash("Enter the 6-digit code you received.", "danger")
            return render_template("auth/verify_otp.html",
                                   email=session.get("pending_user_email"))

        result = otp_repo.verify_and_consume(pending_id, code_attempt, purpose="login")

        if result == "ok":
            # Promote pending user to a real session
            conn = get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, name, role FROM users WHERE id = %s",
                        (pending_id,),
                    )
                    user = cursor.fetchone()
            finally:
                conn.close()

            if user is None:
                session.clear()
                flash("Your account could not be found.", "danger")
                return redirect(url_for("auth.login"))

            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = user["role"]

            flash(f"Welcome back, {user['name']}.", "success")
            return redirect(url_for("dashboard.dashboard"))

        elif result == "expired":
            flash("That code has expired. Please log in again.", "danger")
            session.clear()
            return redirect(url_for("auth.login"))

        elif result == "exhausted":
            flash("Too many wrong attempts. Please log in again.", "danger")
            session.clear()
            return redirect(url_for("auth.login"))

        elif result == "missing":
            flash("No active code. Please log in again.", "danger")
            session.clear()
            return redirect(url_for("auth.login"))

        else:  # invalid
            flash("Incorrect code. Try again.", "danger")
            return render_template("auth/verify_otp.html",
                                   email=session.get("pending_user_email"))

    return render_template("auth/verify_otp.html",
                           email=session.get("pending_user_email"))


# ==========================================================================
# RESEND OTP
# ==========================================================================
def resendOtp():
    """Re-issue a fresh OTP for the pending user."""
    pending_id = session.get("pending_user_id")
    if not pending_id:
        flash("Please log in first.", "warning")
        return redirect(url_for("auth.login"))

    email = session.get("pending_user_email")
    code = otp_repo.create_for_user(pending_id, purpose="login")
    send_otp_via_console(email, code)

    flash("A new code has been sent.", "success")
    return redirect(url_for("auth.verifyOtp"))


# ==========================================================================
# LOGOUT
# ==========================================================================
def logout():
    session.clear()
    flash("You've been logged out.", "success")
    return redirect(url_for("home"))