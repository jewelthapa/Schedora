from flask import Blueprint

from app.controllers import dashboardController

dashboard_bp = Blueprint("dashboard", __name__)


def register_routes():
    dashboard_bp.add_url_rule(
        "/dashboard",
        view_func=dashboardController.dashboard,
        methods=["GET"],
    )


register_routes()