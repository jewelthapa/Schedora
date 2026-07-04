from flask import render_template, request, redirect, url_for, flash, g, abort

from app.auth import login_required
from app.database import get_connection
from app.repository import notification_repo


@login_required
def notifications():
    """Show all notifications for the logged-in user."""
    items = notification_repo.list_for_user(g.current_user["id"])
    return render_template("notifications/list.html", items=items)


@login_required
def markRead(notification_id):
    """Mark a single notification as read. Verifies ownership first."""
    _update_one(notification_id, g.current_user["id"], set_read=True)
    return redirect(url_for("notification.notifications"))


@login_required
def markAllRead():
    """Mark every notification for this user as read."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE",
                (g.current_user["id"],),
            )
            conn.commit()
    finally:
        conn.close()
    flash("All notifications marked as read.", "success")
    return redirect(url_for("notification.notifications"))


@login_required
def deleteOne(notification_id):
    """Delete a single notification. Verifies ownership."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM notifications WHERE id = %s AND user_id = %s",
                (notification_id, g.current_user["id"]),
            )
            if not cursor.fetchone():
                abort(404)
            cursor.execute(
                "DELETE FROM notifications WHERE id = %s AND user_id = %s",
                (notification_id, g.current_user["id"]),
            )
            conn.commit()
    finally:
        conn.close()
    flash("Notification deleted.", "success")
    return redirect(url_for("notification.notifications"))


@login_required
def createTest():
    """Dev helper: create a fake notification so we can see the flow work
    before bookings exist. Remove this route before production."""
    notification_repo.create(
        g.current_user["id"],
        "This is a test notification.",
        "info",
    )
    flash("Test notification created.", "success")
    return redirect(url_for("notification.notifications"))


def _update_one(notification_id, user_id, set_read):
    """Safely update a notification only if it belongs to the caller."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM notifications WHERE id = %s AND user_id = %s",
                (notification_id, user_id),
            )
            if not cursor.fetchone():
                abort(404)
            cursor.execute(
                "UPDATE notifications SET is_read = %s WHERE id = %s",
                (set_read, notification_id),
            )
            conn.commit()
    finally:
        conn.close()