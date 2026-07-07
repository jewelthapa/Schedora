from flask import render_template, request, redirect, url_for, flash, g, session
from werkzeug.security import generate_password_hash, check_password_hash

from app.auth import login_required
from app.database import get_connection


@login_required
def profile():
    """Show the profile page for the currently logged-in user."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, name, email, role, phone, bio, created_at,
                          two_factor_enabled
                   FROM users WHERE id = %s""",
                (g.current_user["id"],),
            )
            user = cursor.fetchone()
    finally:
        conn.close()

    if user is None:
        # Session references a user that no longer exists — log them out.
        session.clear()
        flash("Your account could not be found.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("profile/profile.html", user=user)


@login_required
def editProfile():
    """Update the logged-in user's profile (name, email, phone, bio,
    two-factor auth toggle, optional password change). Requires the
    current password to confirm any change — small but real security measure."""
    user_id = g.current_user["id"]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        bio = request.form.get("bio", "").strip()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        two_factor_enabled = 1 if request.form.get("two_factor_enabled") == "on" else 0

        # --- Basic validation ---
        errors = []
        if len(name) < 2:
            errors.append("Name must be at least 2 characters.")
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")
        if new_password and len(new_password) < 6:
            errors.append("New password must be at least 6 characters.")

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                # Load current user for password check + email conflict check
                cursor.execute(
                    "SELECT id, email, password FROM users WHERE id = %s",
                    (user_id,),
                )
                user = cursor.fetchone()

                if user is None:
                    session.clear()
                    flash("Account not found.", "danger")
                    return redirect(url_for("auth.login"))

                # Password confirmation required for ANY change
                if not check_password_hash(user["password"], current_password):
                    errors.append("Current password is incorrect.")

                # Email uniqueness (only if email actually changed)
                if email != user["email"]:
                    cursor.execute(
                        "SELECT id FROM users WHERE email = %s AND id != %s",
                        (email, user_id),
                    )
                    if cursor.fetchone():
                        errors.append("That email is already in use.")

                if errors:
                    for e in errors:
                        flash(e, "danger")
                    # Reload the fresh user to re-render the form
                    cursor.execute(
                        """SELECT id, name, email, role, phone, bio, created_at,
                                  two_factor_enabled
                           FROM users WHERE id = %s""",
                        (user_id,),
                    )
                    user_fresh = cursor.fetchone()
                    # Overwrite with what they submitted so they don't lose typing
                    user_fresh.update({
                        "name": name, "email": email,
                        "phone": phone, "bio": bio,
                        "two_factor_enabled": two_factor_enabled,
                    })
                    return render_template("profile/edit.html", user=user_fresh)

                # --- Apply update ---
                if new_password:
                    hashed = generate_password_hash(new_password)
                    cursor.execute(
                        """UPDATE users
                           SET name = %s, email = %s, phone = %s, bio = %s,
                               password = %s, two_factor_enabled = %s
                           WHERE id = %s""",
                        (name, email, phone, bio, hashed,
                         two_factor_enabled, user_id),
                    )
                else:
                    cursor.execute(
                        """UPDATE users
                           SET name = %s, email = %s, phone = %s, bio = %s,
                               two_factor_enabled = %s
                           WHERE id = %s""",
                        (name, email, phone, bio,
                         two_factor_enabled, user_id),
                    )
                conn.commit()

                # Keep the session in sync with the new name
                session["user_name"] = name
        finally:
            conn.close()

        flash("Profile updated.", "success")
        return redirect(url_for("profile.profile"))

    # GET — load current values and show edit form
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, name, email, role, phone, bio, created_at,
                          two_factor_enabled
                   FROM users WHERE id = %s""",
                (user_id,),
            )
            user = cursor.fetchone()
    finally:
        conn.close()

    return render_template("profile/edit.html", user=user)