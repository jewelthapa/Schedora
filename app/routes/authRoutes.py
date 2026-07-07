from flask import Blueprint

from app.controllers import authController

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def register_routes():
    # Register supports both GET (show form) and POST (submit)
    auth_bp.add_url_rule(
        "/register",
        view_func=authController.register,
        methods=["GET", "POST"],
    )
def register_routes():
    auth_bp.add_url_rule(
        "/register",
        view_func=authController.register,
        methods=["GET", "POST"],
    )
    auth_bp.add_url_rule(
        "/login",
        view_func=authController.login,
        methods=["GET", "POST"],
    )
    auth_bp.add_url_rule(
        "/logout",
        view_func=authController.logout,
        methods=["GET"],
    )
    auth_bp.add_url_rule(
        "/verify-otp",
        view_func=authController.verifyOtp,
        methods=["GET", "POST"],
        endpoint="verifyOtp",
    )
    auth_bp.add_url_rule(
        "/resend-otp",
        view_func=authController.resendOtp,
        methods=["POST"],
        endpoint="resendOtp",
    )
register_routes()
