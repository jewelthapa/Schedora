from flask import Blueprint

from app.controllers import profileController

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


def register_routes():
    profile_bp.add_url_rule(
        "",
        view_func=profileController.profile,
        methods=["GET"],
        endpoint="profile",
    )
    profile_bp.add_url_rule(
        "/edit",
        view_func=profileController.editProfile,
        methods=["GET", "POST"],
        endpoint="edit",
    )


register_routes()