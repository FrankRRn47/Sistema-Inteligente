from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.user import User

profile_bp = Blueprint("profile", __name__)


def _current_user_id():
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return identity


@profile_bp.get("/profile")
@jwt_required()
def get_profile():
    user_id = _current_user_id()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found."}), HTTPStatus.NOT_FOUND
    return jsonify(user.to_dict())


@profile_bp.put("/profile")
@jwt_required()
def update_profile():
    user_id = _current_user_id()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found."}), HTTPStatus.NOT_FOUND

    payload = request.get_json(force=True) or {}
    if "full_name" in payload:
        user.full_name = payload["full_name"].strip() or user.full_name
    if payload.get("password"):
        user.set_password(payload["password"])
    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()})
