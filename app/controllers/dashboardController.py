from flask import render_template, g

from app.auth import login_required
from app.database import get_connection


@login_required
def dashboard():
    """Show the dashboard for the currently logged-in user.

    Renders one of two templates depending on the user's role,
    with real stats and recent activity pulled from MySQL.
    """
    user = g.current_user
    if user["role"] == "provider":
        stats, recent = _provider_data(user["id"])
        return render_template("dashboard/provider.html",
                               user=user, stats=stats, recent_bookings=recent)
    stats, recent = _client_data(user["id"])
    return render_template("dashboard/client.html",
                           user=user, stats=stats, recent_bookings=recent)


def _client_data(client_id):
    """Aggregate stat counts + last 5 bookings for a client."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                  SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) AS upcoming,
                  SUM(CASE WHEN status = 'pending'  THEN 1 ELSE 0 END) AS pending,
                  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed
                FROM bookings WHERE client_id = %s
            """, (client_id,))
            counts = cursor.fetchone() or {}

            cursor.execute(
                "SELECT COUNT(*) AS favorites FROM favorites WHERE client_id = %s",
                (client_id,),
            )
            fav = cursor.fetchone() or {}

            cursor.execute("""
                SELECT b.status,
                       s.title  AS service_title,
                       u.name   AS provider_name,
                       t.slot_date, t.start_time
                FROM bookings b
                JOIN services   s ON s.id = b.service_id
                JOIN users      u ON u.id = b.provider_id
                JOIN time_slots t ON t.id = b.time_slot_id
                WHERE b.client_id = %s
                ORDER BY b.created_at DESC
                LIMIT 5
            """, (client_id,))
            recent = cursor.fetchall()
    finally:
        conn.close()

    stats = {
        "upcoming":  counts.get("upcoming")  or 0,
        "pending":   counts.get("pending")   or 0,
        "completed": counts.get("completed") or 0,
        "favorites": fav.get("favorites")    or 0,
    }
    return stats, recent


def _provider_data(provider_id):
    """Aggregate stat counts + last 5 incoming bookings for a provider."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                  SUM(CASE WHEN status = 'pending'  THEN 1 ELSE 0 END) AS pending,
                  SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) AS confirmed
                FROM bookings WHERE provider_id = %s
            """, (provider_id,))
            counts = cursor.fetchone() or {}

            cursor.execute(
                "SELECT COUNT(*) AS n FROM services WHERE provider_id = %s",
                (provider_id,),
            )
            svc = cursor.fetchone() or {}

            cursor.execute(
                "SELECT COUNT(*) AS n FROM time_slots WHERE provider_id = %s AND is_booked = FALSE",
                (provider_id,),
            )
            slots = cursor.fetchone() or {}

            cursor.execute("""
                SELECT b.status,
                       s.title  AS service_title,
                       u.name   AS client_name,
                       t.slot_date, t.start_time
                FROM bookings b
                JOIN services   s ON s.id = b.service_id
                JOIN users      u ON u.id = b.client_id
                JOIN time_slots t ON t.id = b.time_slot_id
                WHERE b.provider_id = %s
                ORDER BY b.created_at DESC
                LIMIT 5
            """, (provider_id,))
            recent = cursor.fetchall()
    finally:
        conn.close()

    stats = {
        "pending":    counts.get("pending")    or 0,
        "confirmed":  counts.get("confirmed")  or 0,
        "services":   svc.get("n")             or 0,
        "open_slots": slots.get("n")           or 0,
    }
    return stats, recent