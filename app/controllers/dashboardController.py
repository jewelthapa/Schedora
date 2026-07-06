"""
Dashboard controller.
Serves role-aware dashboard pages for the logged-in user.
"""

from flask import render_template, g

from app.auth import login_required
from app.database import get_connection


@login_required
def dashboard():
    role = g.current_user["role"]
    stats, recent_bookings = _load_dashboard_data(role, g.current_user["id"])

    if role == "provider":
        return render_template(
            "dashboard/provider.html",
            user=g.current_user,
            stats=stats,
            recent_bookings=recent_bookings,
        )

    return render_template(
        "dashboard/client.html",
        user=g.current_user,
        stats=stats,
        recent_bookings=recent_bookings,
    )


# --------------------------------------------------------------------
def _load_dashboard_data(role, user_id):
    """Load stat counts + a short list of recent bookings, role-aware."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if role == "provider":
                # Provider stat counts
                cursor.execute(
                    """
                    SELECT
                        SUM(CASE WHEN b.status = 'pending'  THEN 1 ELSE 0 END) AS pending,
                        SUM(CASE WHEN b.status = 'accepted' THEN 1 ELSE 0 END) AS confirmed
                    FROM bookings b
                    WHERE b.provider_id = %s
                    """,
                    (user_id,),
                )
                base = cursor.fetchone() or {}
                stats = {
                    "pending":   int(base.get("pending")   or 0),
                    "confirmed": int(base.get("confirmed") or 0),
                }

                cursor.execute(
                    "SELECT COUNT(*) AS c FROM services WHERE provider_id = %s",
                    (user_id,),
                )
                stats["services"] = int((cursor.fetchone() or {}).get("c", 0))

                cursor.execute(
                    """
                    SELECT COUNT(*) AS c
                    FROM time_slots
                    WHERE provider_id = %s
                      AND is_booked = FALSE
                      AND slot_date >= CURDATE()
                    """,
                    (user_id,),
                )
                stats["open_slots"] = int((cursor.fetchone() or {}).get("c", 0))

                cursor.execute(
                    """
                    SELECT b.status,
                           s.title AS service_title,
                           u.name  AS client_name,
                           t.slot_date, t.start_time
                    FROM bookings b
                    JOIN services  s ON s.id = b.service_id
                    JOIN users     u ON u.id = b.client_id
                    JOIN time_slots t ON t.id = b.time_slot_id
                    WHERE b.provider_id = %s
                    ORDER BY b.created_at DESC
                    LIMIT 5
                    """,
                    (user_id,),
                )
                recent_bookings = cursor.fetchall()

            else:
                # Client stat counts
                cursor.execute(
                    """
                    SELECT
                        SUM(CASE WHEN status = 'accepted'  THEN 1 ELSE 0 END) AS upcoming,
                        SUM(CASE WHEN status = 'pending'   THEN 1 ELSE 0 END) AS pending,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed
                    FROM bookings
                    WHERE client_id = %s
                    """,
                    (user_id,),
                )
                base = cursor.fetchone() or {}
                stats = {
                    "upcoming":  int(base.get("upcoming")  or 0),
                    "pending":   int(base.get("pending")   or 0),
                    "completed": int(base.get("completed") or 0),
                }

                # Favorites count
                cursor.execute(
                    "SELECT COUNT(*) AS c FROM favorites WHERE client_id = %s",
                    (user_id,),
                )
                stats["favorites"] = int((cursor.fetchone() or {}).get("c", 0))

                cursor.execute(
                    """
                    SELECT b.status,
                           s.title AS service_title,
                           u.name  AS provider_name,
                           t.slot_date, t.start_time
                    FROM bookings b
                    JOIN services  s ON s.id = b.service_id
                    JOIN users     u ON u.id = b.provider_id
                    JOIN time_slots t ON t.id = b.time_slot_id
                    WHERE b.client_id = %s
                    ORDER BY b.created_at DESC
                    LIMIT 5
                    """,
                    (user_id,),
                )
                recent_bookings = cursor.fetchall()

    finally:
        conn.close()

    return stats, recent_bookings