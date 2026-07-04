from flask import Blueprint

from app.controllers import serviceController

service_bp = Blueprint("service", __name__, url_prefix="/services")


def register_routes():
    service_bp.add_url_rule(
        "",
        view_func=serviceController.myServices,
        methods=["GET"],
        endpoint="myServices",
    )
    service_bp.add_url_rule(
        "/new",
        view_func=serviceController.createService,
        methods=["GET", "POST"],
        endpoint="createService",
    )
    service_bp.add_url_rule(
        "/<int:service_id>/edit",
        view_func=serviceController.editService,
        methods=["GET", "POST"],
        endpoint="editService",
    )
    service_bp.add_url_rule(
        "/<int:service_id>/delete",
        view_func=serviceController.deleteService,
        methods=["POST"],
        endpoint="deleteService",
    )


register_routes()