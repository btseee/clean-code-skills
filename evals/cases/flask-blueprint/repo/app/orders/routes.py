from flask import Blueprint, jsonify

from .services import list_orders

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.route("/", methods=["GET"])
def get_orders():
    return jsonify(list_orders())
