from datetime import date

from flask import render_template, request, redirect, url_for, flash, g, abort

from app.auth import login_required, role_required
from app.database import get_connection
from app.repository import notification_repo


@login_required
@role_required("client")
def createBooking():
    """Two-step booking flow:
       GET  /bookings/new?slot_id=X → shows a confirmation page
       POST /bookings/new           → actually creates the booking
    """
    slot_id = request.values.get("slot_id", type=int)
    if not slot_id:
        flash("No slot selected.", "danger")
        return redirect(url_for("browse.browse"))

    # Fetch slot + service + provider for the confirmation view
    slot = _get_bookable_slot_or_404(slot_id)

    if request.method == "POST":
        # Re-check availability at commit time to prevent race conditions
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                # Lock and re-check
                cursor.execute(
                    "SELECT is_booked FROM time_slots WHERE id = %s FOR UPDATE",
                    (slot_id,),
                )
                row = cursor.fetchone()
                if row is None or row["is_booked"]:
                    conn.rollback()
                    flash("Sorry, that slot was just booked by someone else.", "warning")
                    return redirect(url_for("browse.detail", service_id=slot["service_id"]))

                # Atomic: insert booking + flip slot as booked
                cursor.execute(
                    """INSERT INTO bookings
                        (client_id, provider_id, service_id, time_slot_id, status)
                       VALUES (%s, %s, %s, %s, 'pending')""",
                    (g.current_user["id"], slot["provider_id"],
                     slot["service_id"], slot_id),
                )
                cursor.execute(
                    "UPDATE time_slots SET is_booked = TRUE WHERE id = %s",
                    (slot_id,),
                )
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        # Notify the provider — outside the transaction so a notification
        # failure doesn't roll back the booking
        notification_repo.create(
            slot["provider_id"],
            f"New booking request from {g.current_user['name']} "
            f"for {slot['service_title']} on {slot['slot_date']}.",
            "info",
        )

        flash("Booking request sent. You'll be notified when the provider responds.", "success")
        return redirect(url_for("booking.myBookings"))

    return render_template("bookings/confirm.html", slot=slot)


@login_required
@role_required("client")
def myBookings():
    """List the client's bookings, most recent first.
    Optional ?status= filter."""
    status_filter = request.args.get("status", "").strip()
    valid_statuses = {"pending", "accepted", "rejected", "cancelled", "completed"}

    sql = """
        SELECT b.id, b.status, b.created_at,
               s.title AS service_title, s.category, s.price,
               u.name  AS provider_name,
               t.slot_date, t.start_time, t.end_time
        FROM bookings b
        JOIN services   s ON s.id = b.service_id
        JOIN users      u ON u.id = b.provider_id
        JOIN time_slots t ON t.id = b.time_slot_id
        WHERE b.client_id = %s
    """
    params = [g.current_user["id"]]

    if status_filter in valid_statuses:
        sql += " AND b.status = %s"
        params.append(status_filter)

    sql += " ORDER BY t.slot_date DESC, t.start_time DESC"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            bookings = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        "bookings/my_bookings.html",
        bookings=bookings,
        active_status=status_filter if status_filter in valid_statuses else "",
        today=date.today(),
    )


@login_required
@role_required("client")
def cancelBooking(booking_id):
    """Client cancels a pending or accepted booking.
    Frees the slot and notifies the provider."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Ownership check + fetch what we need
            cursor.execute(
                """SELECT b.id, b.status, b.provider_id, b.time_slot_id,
                          s.title AS service_title
                   FROM bookings b
                   JOIN services s ON s.id = b.service_id
                   WHERE b.id = %s AND b.client_id = %s""",
                (booking_id, g.current_user["id"]),
            )
            booking = cursor.fetchone()
            if booking is None:
                abort(404)

            if booking["status"] not in ("pending", "accepted"):
                flash(f"This booking is already {booking['status']} and can't be cancelled.",
                      "warning")
                return redirect(url_for("booking.myBookings"))

            # Atomic: flip status + free the slot
            cursor.execute(
                "UPDATE bookings SET status = 'cancelled' WHERE id = %s",
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

    # Notify the provider
    notification_repo.create(
        booking["provider_id"],
        f"{g.current_user['name']} cancelled their booking for {booking['service_title']}.",
        "warning",
    )

    flash("Booking cancelled.", "success")
    return redirect(url_for("booking.myBookings"))


# -------------------------------------------------------------------- helpers
def _get_bookable_slot_or_404(slot_id):
    """Load slot + service + provider info. Only bookable slots (not yet
    booked, not in the past) are returned."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT t.id, t.slot_date, t.start_time, t.end_time, t.is_booked,
                          s.id AS service_id, s.title AS service_title,
                          s.description, s.category, s.price,
                          u.id AS provider_id, u.name AS provider_name
                   FROM time_slots t
                   JOIN services s ON s.id = t.service_id
                   JOIN users u   ON u.id = t.provider_id
                   WHERE t.id = %s""",
                (slot_id,),
            )
            row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        abort(404)
    if row["is_booked"]:
        abort(404)  # treat already-booked as "not available"
    return row