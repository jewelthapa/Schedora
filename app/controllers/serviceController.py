from flask import render_template, request, redirect, url_for, flash, g, abort

from app.auth import login_required, role_required
from app.database import get_connection


# ---------- CATEGORIES (matches home page) ----------
CATEGORIES = [
    "Doctors", "Salons", "Tutors", "Gyms",
    "Photographers", "Mechanics", "Lawyers", "Trainers",
]


@login_required
@role_required("provider")
def myServices():
    """List the services this provider has created."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, title, description, category, price, created_at
                   FROM services
                   WHERE provider_id = %s
                   ORDER BY created_at DESC""",
                (g.current_user["id"],),
            )
            services = cursor.fetchall()
    finally:
        conn.close()
    return render_template("services/my_services.html", services=services)


@login_required
@role_required("provider")
def createService():
    """Create a new service listing."""
    if request.method == "POST":
        title, description, category, price, errors = _read_form()
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "services/service_form.html",
                mode="create",
                categories=CATEGORIES,
                service={"title": title, "description": description,
                         "category": category, "price": price},
            )

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO services (provider_id, title, description, category, price)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (g.current_user["id"], title, description, category, price),
                )
                conn.commit()
        finally:
            conn.close()

        flash("Service created.", "success")
        return redirect(url_for("service.myServices"))

    # GET
    return render_template(
        "services/service_form.html",
        mode="create",
        categories=CATEGORIES,
        service=None,
    )


@login_required
@role_required("provider")
def editService(service_id):
    """Edit an existing service. Provider can only edit their own."""
    service = _get_own_service_or_404(service_id, g.current_user["id"])

    if request.method == "POST":
        title, description, category, price, errors = _read_form()
        if errors:
            for e in errors:
                flash(e, "danger")
            # Re-render with the values they just typed
            return render_template(
                "services/service_form.html",
                mode="edit",
                categories=CATEGORIES,
                service={"id": service_id, "title": title,
                         "description": description, "category": category,
                         "price": price},
            )

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE services
                       SET title = %s, description = %s, category = %s, price = %s
                       WHERE id = %s AND provider_id = %s""",
                    (title, description, category, price,
                     service_id, g.current_user["id"]),
                )
                conn.commit()
        finally:
            conn.close()

        flash("Service updated.", "success")
        return redirect(url_for("service.myServices"))

    # GET
    return render_template(
        "services/service_form.html",
        mode="edit",
        categories=CATEGORIES,
        service=service,
    )


@login_required
@role_required("provider")
def deleteService(service_id):
    """Delete a service. Only the owning provider can delete it."""
    _get_own_service_or_404(service_id, g.current_user["id"])

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM services WHERE id = %s AND provider_id = %s",
                (service_id, g.current_user["id"]),
            )
            conn.commit()
    finally:
        conn.close()

    flash("Service deleted.", "success")
    return redirect(url_for("service.myServices"))


# ---------- helpers ----------
def _read_form():
    """Read + validate the shared create/edit form. Returns
    (title, description, category, price, errors)."""
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()
    price_raw = request.form.get("price", "").strip()

    errors = []
    if len(title) < 3:
        errors.append("Title must be at least 3 characters.")
    if category not in CATEGORIES:
        errors.append("Please pick a valid category.")

    price = 0
    try:
        price = float(price_raw)
        if price < 0:
            errors.append("Price cannot be negative.")
    except ValueError:
        errors.append("Price must be a number.")

    return title, description, category, price, errors


def _get_own_service_or_404(service_id, provider_id):
    """Fetch a service, but only if it belongs to this provider.
    Returns the row or aborts with 404."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, title, description, category, price
                   FROM services
                   WHERE id = %s AND provider_id = %s""",
                (service_id, provider_id),
            )
            row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        abort(404)
    return row