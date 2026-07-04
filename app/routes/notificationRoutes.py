from flask import Blueprint

from app.controllers import notificationController

notification_bp = Blueprint("notification", __name__, url_prefix="/notifications")


def register_routes():
    notification_bp.add_url_rule(
        "",
        view_func=notificationController.notifications,
        methods=["GET"],
        endpoint="notifications",
    )
    notification_bp.add_url_rule(
        "/<int:notification_id>/read",
        view_func=notificationController.markRead,
        methods=["POST"],
        endpoint="markRead",
    )
    notification_bp.add_url_rule(
        "/read-all",
        view_func=notificationController.markAllRead,
        methods=["POST"],
        endpoint="markAllRead",
    )
    notification_bp.add_url_rule(
        "/<int:notification_id>/delete",
        view_func=notificationController.deleteOne,
        methods=["POST"],
        endpoint="deleteOne",
    )
    notification_bp.add_url_rule(
        "/test",
        view_func=notificationController.createTest,
        methods=["GET"],
        endpoint="createTest",
    )


register_routes()