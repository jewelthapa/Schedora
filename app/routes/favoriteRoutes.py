from flask import Blueprint

from app.controllers import favoriteController

favorite_bp = Blueprint("favorite", __name__, url_prefix="/favorites")


def register_routes():
    favorite_bp.add_url_rule(
        "",
        view_func=favoriteController.myFavorites,
        methods=["GET"],
        endpoint="myFavorites",
    )
    favorite_bp.add_url_rule(
        "/toggle/<int:provider_id>",
        view_func=favoriteController.toggleFavorite,
        methods=["POST"],
        endpoint="toggleFavorite",
    )


register_routes()