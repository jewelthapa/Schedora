from datetime import date

from flask import render_template, request, redirect, url_for, flash, g, abort

from app.auth import login_required, role_required
from app.database import get_connection
from app.repository import notification_repo


@login_required
@role_required("client")
def createReview(booking_id):
    """Client leaves a review for a past accepted booking.

    Guards:
      - booking must belong to the client
      - booking must be accepted or completed
      - slot date must have passed
      - no existing review (enforced by DB unique + our check)
    """
    booking = _get_reviewable_booking_or_error(booking_id, g.current_user["id"])
    if booking is None:
        return redirect(url_for("booking.myBookings"))

    if request.method == "POST":
        rating_raw = request.form.get("rating", "").strip()
        comment = request.form.get("comment", "").strip()

        errors = []
        try:
            rating = int(rating_raw)
            if rating < 1 or rating > 5:
                errors.append("Rating must be between 1 and 5.")
        except ValueError:
            rating = 0
            errors.append("Please pick a rating.")

        if len(comment) > 500:
            errors.append("Comment can be at most 500 characters.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("reviews/create.html",
                                   booking=booking, rating=rating, comment=comment)

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                # Insert the review
                cursor.execute(
                    """INSERT INTO reviews
                        (booking_id, client_id, provider_id, rating, comment)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (booking_id, g.current_user["id"],
                     booking["provider_id"], rating, comment or None),
                )
                conn.commit()
        finally:
            conn.close()

        # Notify the provider
        notification_repo.create(
            booking["provider_id"],
            f"{g.current_user['name']} left a {rating}-star review "
            f"for {booking['service_title']}.",
            "info",
        )

        flash("Thanks for reviewing.", "success")
        return redirect(url_for("booking.myBookings"))

    return render_template("reviews/create.html",
                           booking=booking, rating=0, comment="")


@login_required
@role_required("provider")
def myReviews():
    """Provider sees all reviews they've received, plus average rating."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT r.id, r.rating, r.comment, r.created_at,
                          u.name AS client_name,
                          s.title AS service_title, s.category
                   FROM reviews r
                   JOIN users u    ON u.id = r.client_id
                   JOIN bookings b ON b.id = r.booking_id
                   JOIN services s ON s.id = b.service_id
                   WHERE r.provider_id = %s
                   ORDER BY r.created_at DESC""",
                (g.current_user["id"],),
            )
            reviews = cursor.fetchall()

            cursor.execute(
                """SELECT
                     COUNT(*) AS total,
                     ROUND(AVG(rating), 1) AS avg_rating
                   FROM reviews WHERE provider_id = %s""",
                (g.current_user["id"],),
            )
            stats = cursor.fetchone() or {"total": 0, "avg_rating": None}
    finally:
        conn.close()

    return render_template("reviews/my_reviews.html",
                           reviews=reviews, stats=stats)


# ---------------------------------------------------------------- helpers
def _get_reviewable_booking_or_error(booking_id, client_id):
    """Fetch a booking, but only if it can be reviewed by this client.

    A booking is reviewable when:
      - it belongs to the client (ownership)
      - status is 'accepted' or 'completed'
      - the slot date is today or earlier
      - no review already exists
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT b.id, b.status, b.provider_id,
                          s.title AS service_title,
                          u.name  AS provider_name,
                          t.slot_date,
                          (SELECT COUNT(*) FROM reviews r
                           WHERE r.booking_id = b.id) AS review_count
                   FROM bookings b
                   JOIN services   s ON s.id = b.service_id
                   JOIN users      u ON u.id = b.provider_id
                   JOIN time_slots t ON t.id = b.time_slot_id
                   WHERE b.id = %s AND b.client_id = %s""",
                (booking_id, client_id),
            )
            booking = cursor.fetchone()
    finally:
        conn.close()

    if booking is None:
        abort(404)

    if booking["status"] not in ("accepted", "completed"):
        flash("You can only review completed appointments.", "warning")
        return None

    if booking["slot_date"] > date.today():
        flash("You can review this after your appointment.", "warning")
        return None

    if booking["review_count"] > 0:
        flash("You've already reviewed this booking.", "warning")
        return None

    return booking