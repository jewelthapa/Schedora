from flask import render_template, request, redirect, url_for, flash, g, abort

from app.auth import login_required, role_required
from app.database import get_connection
from app.repository import notification_repo


@login_required
@role_required("provider")
def incomingBookings():
    """List bookings for this provider, with optional status filter.
    Sort so pending appears first (needs action), then accepted, then rest."""
    status_filter = request.args.get("status", "").strip()
    valid_statuses = {"pending", "accepted", "rejected", "cancelled", "completed"}

    sql = """
        SELECT b.id, b.status, b.created_at,
               s.title AS service_title, s.category, s.price,
               u.name  AS client_name,
               t.slot_date, t.start_time, t.end_time
        FROM bookings b
        JOIN services   s ON s.id = b.service_id
        JOIN users      u ON u.id = b.client_id
        JOIN time_slots t ON t.id = b.time_slot_id
        WHERE b.provider_id = %s
    """
    params = [g.current_user["id"]]

    if status_filter in valid_statuses:
        sql += " AND b.status = %s"
        params.append(status_filter)

    # Sort: pending first (need action), then accepted, then everything else
    sql += """
        ORDER BY
          CASE b.status
            WHEN 'pending'  THEN 1
            WHEN 'accepted' THEN 2
            ELSE 3
          END,
          t.slot_date ASC, t.start_time ASC
    """

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            bookings = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        "bookings/incoming.html",
        bookings=bookings,
        active_status=status_filter if status_filter in valid_statuses else "",
    )


@login_required
@role_required("provider")
def acceptBooking(booking_id):
    """Provider accepts a pending booking. Slot stays booked, client gets notified."""
    booking = _get_own_pending_booking_or_error(booking_id, g.current_user["id"])
    if booking is None:
        return redirect(url_for("incoming.incomingBookings"))

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE bookings SET status = 'accepted' WHERE id = %s",
                (booking_id,),
            )
            conn.commit()
    finally:
        conn.close()

    # Notify the client
    notification_repo.create(
        booking["client_id"],
        f"{g.current_user['name']} accepted your booking for "
        f"{booking['service_title']} on {booking['slot_date']}.",
        "success",
    )

    flash("Booking accepted. The client has been notified.", "success")
    return redirect(url_for("incoming.incomingBookings"))


@login_required
@role_required("provider")
def rejectBooking(booking_id):
    """Provider rejects a pending booking.
    Frees the slot AND notifies the client."""
    booking = _get_own_pending_booking_or_error(booking_id, g.current_user["id"])
    if booking is None:
        return redirect(url_for("incoming.incomingBookings"))

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Atomic: flip booking + free slot
            cursor.execute(
                "UPDATE bookings SET status = 'rejected' WHERE id = %s",
                (booking_id,),
            )
            cursor.execute(
                "UPDATE time_slots SET is_booked = FALSE WHERE id = %s",
                (booking["time_slot_id"],),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    # Notify the client
    notification_repo.create(
        booking["client_id"],
        f"{g.current_user['name']} declined your booking for "
        f"{booking['service_title']} on {booking['slot_date']}.",
        "danger",
    )

    flash("Booking rejected. The slot is now available again.", "success")
    return redirect(url_for("incoming.incomingBookings"))


# ---------------------------------------------------------------- helpers
def _get_own_pending_booking_or_error(booking_id, provider_id):
    """Fetch a booking, but only if:
       - it belongs to this provider (ownership check)
       - it's currently pending (can't accept/reject a resolved booking)
    Returns the booking dict, or None with a flash message set."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT b.id, b.status, b.client_id, b.time_slot_id,
                          s.title AS service_title,
                          t.slot_date
                   FROM bookings b
                   JOIN services s   ON s.id = b.service_id
                   JOIN time_slots t ON t.id = b.time_slot_id
                   WHERE b.id = %s AND b.provider_id = %s""",
                (booking_id, provider_id),
            )
            booking = cursor.fetchone()
    finally:
        conn.close()

    if booking is None:
        abort(404)  # doesn't exist or doesn't belong to us

    if booking["status"] != "pending":
        flash(f"This booking is already {booking['status']} — no action needed.",
              "warning")
        return None

    return booking