from flask import Blueprint

from app.controllers import browseController

browse_bp = Blueprint("browse", __name__, url_prefix="/browse")


def register_routes():
    browse_bp.add_url_rule(
        "",
        view_func=browseController.browse,
        methods=["GET"],
        endpoint="browse",
    )
    browse_bp.add_url_rule(
        "/service/<int:service_id>",
        view_func=browseController.serviceDetail,
        methods=["GET"],
        endpoint="detail",
    )


register_routes()