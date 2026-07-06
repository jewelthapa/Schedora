from flask import Blueprint

from app.controllers import reviewController

review_bp = Blueprint("review", __name__, url_prefix="/reviews")


def register_routes():
    review_bp.add_url_rule(
        "/booking/<int:booking_id>/new",
        view_func=reviewController.createReview,
        methods=["GET", "POST"],
        endpoint="createReview",
    )
    review_bp.add_url_rule(
        "/mine",
        view_func=reviewController.myReviews,
        methods=["GET"],
        endpoint="myReviews",
    )


register_routes()