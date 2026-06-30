from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_connection


def register():
    """Handle user registration (GET shows form, POST creates account)."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "client")

        # --- Server-side validation ---
        errors = []
        if len(name) < 2:
            errors.append("Name must be at least 2 characters.")
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if role not in ("client", "provider"):
            errors.append("Please choose a valid role.")

        if errors:
            for e in errors:
                flash(e, "danger")
            # Re-render with the values they already typed (except password)
            return render_template("auth/auth.html", start="signup", name=name, email=email, role=role)

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                # Check if the email is already registered
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash("An account with that email already exists.", "danger")
                    return render_template("auth/auth.html", start="signup", name=name, email=email, role=role)

                # Hash the password before storing it (never store plaintext)
                hashed = generate_password_hash(password)

                cursor.execute(
                    "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                    (name, email, hashed, role),
                )
                conn.commit()

            flash("Account created. Please log in.", "success")
            return redirect(url_for("auth.login"))
        finally:
            conn.close()

    # GET request → show the sign-up side of the panel
    return render_template("auth/auth.html", start="signup")


def login():
    """Handle login (GET shows form, POST verifies credentials)."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("auth/auth.html", start="signin", email=email)

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, password, role FROM users WHERE email = %s",
                    (email,),
                )
                user = cursor.fetchone()
        finally:
            conn.close()

        # Verify the user exists AND the password matches the stored hash.
        # We give the same generic message either way, so attackers can't
        # tell whether an email is registered.
        if user is None or not check_password_hash(user["password"], password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/auth.html", start="signin", email=email)

        # Credentials valid → start the session
        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_role"] = user["role"]

        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("home"))

    # GET request → show the sign-in side of the panel
    return render_template("auth/auth.html", start="signin")


def logout():
    """Clear the session and log the user out."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))