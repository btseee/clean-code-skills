from flask import Flask

from .orders.routes import orders_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(orders_bp)
    return app
