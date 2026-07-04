from flask import Blueprint

from app.controllers import helpController

help_bp = Blueprint("help", __name__, url_prefix="/help")


def register_routes():
    help_bp.add_url_rule(
        "",
        view_func=helpController.help_page,
        methods=["GET"],
        endpoint="help",
    )


register_routes()