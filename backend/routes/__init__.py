from flask import Flask

from .analysis import analysis_bp
from .auth import auth_bp
from .media import media_bp
from .profile import profile_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(media_bp)
