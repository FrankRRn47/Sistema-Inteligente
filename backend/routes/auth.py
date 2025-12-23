from http import HTTPStatus
import re

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models.user import User

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_REGEX = re.compile(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,}$")


def _validate_registration_payload(full_name: str, email: str, password: str) -> dict:
    errors = {}
    if len(full_name) < 3:
        errors["full_name"] = "Usa al menos 3 caracteres para el nombre completo."
    if not EMAIL_REGEX.match(email):
        errors["email"] = "Proporciona un correo válido (ej. persona@dominio.com)."
    if not PASSWORD_REGEX.match(password or ""):
        errors["password"] = (
            "La contraseña debe tener mínimo 8 caracteres, 1 mayúscula, 1 número y 1 símbolo."
        )
    return errors


def _validate_login_payload(email: str, password: str) -> dict:
    errors = {}
    if not EMAIL_REGEX.match(email):
        errors["email"] = "El correo no tiene un formato válido."
    if not password:
        errors["password"] = "Debes escribir tu contraseña."
    return errors


def _database_unavailable_response(exc: SQLAlchemyError):
    current_app.logger.exception("Database operation failed", exc_info=exc)
    return (
        jsonify(
            {
                "message": "El servicio de base de datos no responde. Verifica MySQL (root@127.0.0.1:3306).",
            }
        ),
        HTTPStatus.SERVICE_UNAVAILABLE,
    )


def _register_user_logic():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    full_name = (payload.get("full_name") or "").strip()
    password = (payload.get("password") or "")

    errors = _validate_registration_payload(full_name, email, password or "")
    if errors:
        return (
            jsonify({"message": "Datos inválidos", "errors": errors}),
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    try:
        existing_user = User.query.filter_by(email=email).first()
    except SQLAlchemyError as exc:
        return _database_unavailable_response(exc)

    if existing_user:
        return (
            jsonify({"message": "A user with this email already exists."}),
            HTTPStatus.CONFLICT,
        )

    user = User(email=email, full_name=full_name)
    user.set_password(password)
    try:
        db.session.add(user)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return _database_unavailable_response(exc)

    access_token = create_access_token(identity=str(user.id))
    return (
        jsonify({"message": "User registered", "token": access_token, "user": user.to_dict()}),
        HTTPStatus.CREATED,
    )


@auth_bp.post("/register")
def register_user():
    return _register_user_logic()


@auth_bp.post("/api/register")
def register_user_api():
    return _register_user_logic()


def _login_user_logic():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = (payload.get("password") or "")

    errors = _validate_login_payload(email, password)
    if errors:
        return (
            jsonify({"message": "Datos inválidos", "errors": errors}),
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    try:
        user = User.query.filter_by(email=email).first()
    except SQLAlchemyError as exc:
        return _database_unavailable_response(exc)
    if not user or not user.check_password(password):
        return (
            jsonify({"message": "Invalid credentials."}),
            HTTPStatus.UNAUTHORIZED,
        )

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"message": "Login successful", "token": access_token, "user": user.to_dict()})


@auth_bp.post("/login")
def login_user():
    return _login_user_logic()


@auth_bp.post("/api/login")
def login_user_api():
    return _login_user_logic()
