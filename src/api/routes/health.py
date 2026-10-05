from flask import Flask

from src.service.uow import AbstractUOW


def create_health_route(app: Flask):
    @app.route("/healthy", methods=["GET"])
    def healthy():
        return {"status": "healthy"}, 200


def create_readiness_route(app: Flask, uow: AbstractUOW):
    @app.route("/ready", methods=["GET"])
    def ready():
        try:
            with uow as unit_of_work:
                unit_of_work.check_health()
        except Exception:
            return {"status": "not ready"}, 503

        return {"status": "ready"}, 200
