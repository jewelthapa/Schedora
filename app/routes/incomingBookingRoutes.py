from flask import Blueprint

from app.controllers import incomingBookingController

incoming_bp = Blueprint("incoming", __name__, url_prefix="/incoming-bookings")


def register_routes():
    incoming_bp.add_url_rule(
        "",
        view_func=incomingBookingController.incomingBookings,
        methods=["GET"],
        endpoint="incomingBookings",
    )
    incoming_bp.add_url_rule(
        "/<int:booking_id>/accept",
        view_func=incomingBookingController.acceptBooking,
        methods=["POST"],
        endpoint="acceptBooking",
    )
    incoming_bp.add_url_rule(
        "/<int:booking_id>/reject",
        view_func=incomingBookingController.rejectBooking,
        methods=["POST"],
        endpoint="rejectBooking",
    )


register_routes()