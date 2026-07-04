from app.database import get_connection


def count_unread(user_id):
    """Return the number of unread notifications for a user."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS n FROM notifications WHERE user_id = %s AND is_read = FALSE",
                (user_id,),
            )
            row = cursor.fetchone()
            return (row or {}).get("n", 0)
    finally:
        conn.close()


def list_for_user(user_id, limit=50):
    """Fetch a user's notifications, newest first."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, message, type, is_read, created_at
                   FROM notifications
                   WHERE user_id = %s
                   ORDER BY created_at DESC
                   LIMIT %s""",
                (user_id, limit),
            )
            return cursor.fetchall()
    finally:
        conn.close()


def create(user_id, message, type_="info"):
    """Insert a new notification for a user.

    This is called from other controllers when something happens
    (e.g. a booking is accepted). Returns the new notification id."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO notifications (user_id, message, type) VALUES (%s, %s, %s)",
                (user_id, message, type_),
            )
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()