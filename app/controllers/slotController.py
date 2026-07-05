from datetime import datetime, date, time

from flask import render_template, request, redirect, url_for, flash, g, abort

from app.auth import login_required, role_required
from app.database import get_connection


@login_required
@role_required("provider")
def mySlots():
    """List all time slots this provider has opened."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT t.id, t.slot_date, t.start_time, t.end_time, t.is_booked,
                          s.id AS service_id, s.title AS service_title
                   FROM time_slots t
                   JOIN services s ON s.id = t.service_id
                   WHERE t.provider_id = %s
                   ORDER BY t.slot_date DESC, t.start_time DESC""",
                (g.current_user["id"],),
            )
            slots = cursor.fetchall()
    finally:
        conn.close()
    return render_template("slots/my_slots.html", slots=slots)


@login_required
@role_required("provider")
def createSlot():
    """Open a new time slot for one of this provider's services."""
    services = _get_own_services(g.current_user["id"])

    if not services:
        flash("Create a service first before opening slots.", "warning")
        return redirect(url_for("service.myServices"))

    if request.method == "POST":
        service_id, slot_date, start_time, end_time, errors = \
            _read_form(services, g.current_user["id"])

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "slots/slot_form.html",
                mode="create",
                services=services,
                slot={"service_id": service_id, "slot_date": slot_date,
                      "start_time": start_time, "end_time": end_time},
            )

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO time_slots
                        (provider_id, service_id, slot_date, start_time, end_time)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (g.current_user["id"], service_id,
                     slot_date, start_time, end_time),
                )
                conn.commit()
        finally:
            conn.close()

        flash("Time slot added.", "success")
        return redirect(url_for("slot.mySlots"))

    return render_template(
        "slots/slot_form.html",
        mode="create",
        services=services,
        slot=None,
    )


@login_required
@role_required("provider")
def editSlot(slot_id):
    """Edit a slot. Only unbooked slots owned by this provider."""
    slot = _get_own_slot_or_404(slot_id, g.current_user["id"])

    if slot["is_booked"]:
        flash("This slot has been booked and can't be edited.", "warning")
        return redirect(url_for("slot.mySlots"))

    services = _get_own_services(g.current_user["id"])

    if request.method == "POST":
        service_id, slot_date, start_time, end_time, errors = \
            _read_form(services, g.current_user["id"])

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "slots/slot_form.html",
                mode="edit",
                services=services,
                slot={"id": slot_id, "service_id": service_id,
                      "slot_date": slot_date, "start_time": start_time,
                      "end_time": end_time},
            )

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE time_slots
                       SET service_id = %s, slot_date = %s,
                           start_time = %s, end_time = %s
                       WHERE id = %s AND provider_id = %s""",
                    (service_id, slot_date, start_time, end_time,
                     slot_id, g.current_user["id"]),
                )
                conn.commit()
        finally:
            conn.close()

        flash("Time slot updated.", "success")
        return redirect(url_for("slot.mySlots"))

    return render_template(
        "slots/slot_form.html",
        mode="edit",
        services=services,
        slot=slot,
    )


@login_required
@role_required("provider")
def deleteSlot(slot_id):
    """Delete a slot. Booked slots can't be deleted."""
    slot = _get_own_slot_or_404(slot_id, g.current_user["id"])

    if slot["is_booked"]:
        flash("This slot has been booked and can't be deleted.", "warning")
        return redirect(url_for("slot.mySlots"))

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM time_slots WHERE id = %s AND provider_id = %s",
                (slot_id, g.current_user["id"]),
            )
            conn.commit()
    finally:
        conn.close()

    flash("Time slot deleted.", "success")
    return redirect(url_for("slot.mySlots"))


# -------------------------------------------------------------------- helpers
def _get_own_services(provider_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title FROM services WHERE provider_id = %s ORDER BY title",
                (provider_id,),
            )
            return cursor.fetchall()
    finally:
        conn.close()


def _get_own_slot_or_404(slot_id, provider_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, service_id, slot_date, start_time, end_time, is_booked
                   FROM time_slots
                   WHERE id = %s AND provider_id = %s""",
                (slot_id, provider_id),
            )
            row = cursor.fetchone()
    finally:
        conn.close()
    if row is None:
        abort(404)
    return row


def _read_form(services, provider_id):
    """Validate submitted slot form. Also checks:
       - service belongs to this provider
       - slot date is not in the past
       - end_time is after start_time
       - no overlap with existing slots for the same service
    """
    service_id_raw = request.form.get("service_id", "").strip()
    date_raw = request.form.get("slot_date", "").strip()
    start_raw = request.form.get("start_time", "").strip()
    end_raw = request.form.get("end_time", "").strip()

    errors = []

    # --- service check ---
    try:
        service_id = int(service_id_raw)
    except ValueError:
        service_id = 0
        errors.append("Please pick a service.")

    if service_id and service_id not in {s["id"] for s in services}:
        errors.append("That service doesn't belong to you.")

    # --- date check ---
    slot_date = None
    try:
        slot_date = datetime.strptime(date_raw, "%Y-%m-%d").date()
        if slot_date < date.today():
            errors.append("Slot date can't be in the past.")
    except ValueError:
        errors.append("Please pick a valid date.")

    # --- time check ---
    start_time = end_time = None
    try:
        start_time = datetime.strptime(start_raw, "%H:%M").time()
        end_time = datetime.strptime(end_raw, "%H:%M").time()
        if end_time <= start_time:
            errors.append("End time must be after start time.")
    except ValueError:
        errors.append("Please pick valid start and end times.")

    # --- overlap check (only if the basics passed) ---
    if not errors:
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                editing_id = request.form.get("editing_id", "0")
                try:
                    editing_id = int(editing_id)
                except ValueError:
                    editing_id = 0

                cursor.execute(
                    """SELECT id FROM time_slots
                       WHERE service_id = %s
                         AND slot_date = %s
                         AND id != %s
                         AND start_time < %s
                         AND end_time > %s""",
                    (service_id, slot_date, editing_id, end_time, start_time),
                )
                if cursor.fetchone():
                    errors.append("This overlaps with another slot for the same service.")
        finally:
            conn.close()

    return service_id, slot_date, start_time, end_time, errors