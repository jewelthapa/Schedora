from flask import Blueprint

from app.controllers import slotController

slot_bp = Blueprint("slot", __name__, url_prefix="/slots")


def register_routes():
    slot_bp.add_url_rule(
        "",
        view_func=slotController.mySlots,
        methods=["GET"],
        endpoint="mySlots",
    )
    slot_bp.add_url_rule(
        "/new",
        view_func=slotController.createSlot,
        methods=["GET", "POST"],
        endpoint="createSlot",
    )
    slot_bp.add_url_rule(
        "/<int:slot_id>/edit",
        view_func=slotController.editSlot,
        methods=["GET", "POST"],
        endpoint="editSlot",
    )
    slot_bp.add_url_rule(
        "/<int:slot_id>/delete",
        view_func=slotController.deleteSlot,
        methods=["POST"],
        endpoint="deleteSlot",
    )


register_routes()