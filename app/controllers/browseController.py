from flask import render_template, request, abort

from app.auth import login_required
from app.database import get_connection


CATEGORIES = [
    "Doctors", "Salons", "Tutors", "Gyms",
    "Photographers", "Mechanics", "Lawyers", "Trainers",
]


@login_required
def browse():
    """List all services, optionally filtered by category or search term.

    URL params:
      ?category=Salons     — filter by category
      ?q=hair              — search by title/description keyword
    """
    category = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()

    # Build the query dynamically depending on filters
    sql = """
        SELECT s.id, s.title, s.description, s.category, s.price,
               u.id AS provider_id, u.name AS provider_name,
               (SELECT COUNT(*) FROM time_slots t
                WHERE t.service_id = s.id
                  AND t.is_booked = FALSE
                  AND t.slot_date >= CURDATE()) AS open_slots
        FROM services s
        JOIN users u ON u.id = s.provider_id
        WHERE 1 = 1
    """
    params = []

    if category and category in CATEGORIES:
        sql += " AND s.category = %s"
        params.append(category)

    if search:
        sql += " AND (s.title LIKE %s OR s.description LIKE %s)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term])

    sql += " ORDER BY open_slots DESC, s.created_at DESC"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            services = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        "browse/browse.html",
        services=services,
        categories=CATEGORIES,
        active_category=category,
        search_term=search,
    )


@login_required
def serviceDetail(service_id):
    """Show one service's details plus all future open slots."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Service + provider info
            cursor.execute(
                """SELECT s.id, s.title, s.description, s.category, s.price,
                          s.created_at,
                          u.id AS provider_id, u.name AS provider_name,
                          u.bio AS provider_bio, u.phone AS provider_phone
                   FROM services s
                   JOIN users u ON u.id = s.provider_id
                   WHERE s.id = %s""",
                (service_id,),
            )
            service = cursor.fetchone()

            if service is None:
                abort(404)

            # Open, future slots for this service
            cursor.execute(
                """SELECT id, slot_date, start_time, end_time
                   FROM time_slots
                   WHERE service_id = %s
                     AND is_booked = FALSE
                     AND slot_date >= CURDATE()
                   ORDER BY slot_date ASC, start_time ASC""",
                (service_id,),
            )
            slots = cursor.fetchall()
    finally:
        conn.close()

    return render_template("browse/detail.html", service=service, slots=slots)