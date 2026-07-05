from flask import Blueprint

from app.controllers import bookingController

booking_bp = Blueprint("booking", __name__, url_prefix="/bookings")


def register_routes():
    booking_bp.add_url_rule(
        "/new",
        view_func=bookingController.createBooking,
        methods=["GET", "POST"],
        endpoint="createBooking",
    )
    booking_bp.add_url_rule(
        "",
        view_func=bookingController.myBookings,
        methods=["GET"],
        endpoint="myBookings",
    )
    booking_bp.add_url_rule(
        "/<int:booking_id>/cancel",
        view_func=bookingController.cancelBooking,
        methods=["POST"],
        endpoint="cancelBooking",
    )


register_routes()