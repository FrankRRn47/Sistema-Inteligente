from http import HTTPStatus

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import get_config
from extensions import init_extensions
from routes import register_blueprints
from utils.db_utils import ensure_database_exists, ensure_database_online


def create_app(env_name: str | None = None) -> Flask:
    app = Flask(__name__)
    @app.get("/")
    def root():
        return jsonify({"message": "Bienvenido a la API de EmocionesDos. El backend está activo."})
    app.config.from_object(get_config(env_name))

    primary_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    fallback_uri = app.config.get("SQLALCHEMY_FALLBACK_URI")
    allow_fallback = app.config.get("ALLOW_DB_FALLBACK", app.debug)
    active_uri = primary_uri

    try:
        ensure_database_exists(primary_uri)
        ensure_database_online(primary_uri)
    except RuntimeError as exc:
        app.logger.warning("Base de datos principal no disponible: %s", exc)
        if not allow_fallback or not fallback_uri or fallback_uri == primary_uri:
            raise
        ensure_database_exists(fallback_uri)
        ensure_database_online(fallback_uri)
        active_uri = fallback_uri
        app.logger.warning("Usando base de datos fallback en %s", active_uri)

    app.config["SQLALCHEMY_DATABASE_URI"] = active_uri
    app.config["PRIMARY_DATABASE_URI"] = primary_uri
    app.config["ACTIVE_DATABASE_URI"] = active_uri
    app.logger.info("Base de datos activa: %s", active_uri)

    init_extensions(app)
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization"],
    )

    with app.app_context():
        # Import models so migrations see them
        import models  # noqa: F401

    register_blueprints(app)
    _register_error_handlers(app)

    @app.get("/health")
    def healthcheck():
        return jsonify({"status": "ok"})

    return app


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        response = {"message": error.description or error.name}
        return jsonify(response), error.code

    @app.errorhandler(Exception)
    def handle_generic_error(error: Exception):
        app.logger.exception("Unhandled error", exc_info=error)
        return jsonify({"message": "Unexpected server error."}), HTTPStatus.INTERNAL_SERVER_ERROR


if __name__ == "__main__":
    application = create_app()
    application.run(host="127.0.0.1", port=5005, debug=True)
