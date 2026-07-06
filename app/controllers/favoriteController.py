from flask import render_template, request, redirect, url_for, flash, g, abort

from app.auth import login_required, role_required
from app.database import get_connection


@login_required
@role_required("client")
def myFavorites():
    """Show all providers the client has saved."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT u.id AS provider_id, u.name, u.bio, u.phone,
                          f.created_at AS saved_at,
                          (SELECT COUNT(*) FROM services s
                           WHERE s.provider_id = u.id) AS service_count,
                          (SELECT ROUND(AVG(rating), 1) FROM reviews r
                           WHERE r.provider_id = u.id) AS avg_rating,
                          (SELECT COUNT(*) FROM reviews r
                           WHERE r.provider_id = u.id) AS review_count
                   FROM favorites f
                   JOIN users u ON u.id = f.provider_id
                   WHERE f.client_id = %s
                   ORDER BY f.created_at DESC""",
                (g.current_user["id"],),
            )
            favorites = cursor.fetchall()
    finally:
        conn.close()

    return render_template("favorites/list.html", favorites=favorites)


@login_required
@role_required("client")
def toggleFavorite(provider_id):
    """Add or remove a provider from favorites.
    Redirects back to where they came from."""
    # Verify the provider exists (and is actually a provider)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name FROM users WHERE id = %s AND role = 'provider'",
                (provider_id,),
            )
            provider = cursor.fetchone()
            if provider is None:
                abort(404)

            # Check if already favorited
            cursor.execute(
                "SELECT id FROM favorites WHERE client_id = %s AND provider_id = %s",
                (g.current_user["id"], provider_id),
            )
            existing = cursor.fetchone()

            if existing:
                # Unsave
                cursor.execute(
                    "DELETE FROM favorites WHERE client_id = %s AND provider_id = %s",
                    (g.current_user["id"], provider_id),
                )
                conn.commit()
                flash(f"Removed {provider['name']} from favourites.", "success")
            else:
                # Save
                cursor.execute(
                    "INSERT INTO favorites (client_id, provider_id) VALUES (%s, %s)",
                    (g.current_user["id"], provider_id),
                )
                conn.commit()
                flash(f"Added {provider['name']} to favourites.", "success")
    finally:
        conn.close()

    # Redirect back to where they came from (fallback to favorites list)
    next_url = request.form.get("next") or url_for("favorite.myFavorites")
    return redirect(next_url)