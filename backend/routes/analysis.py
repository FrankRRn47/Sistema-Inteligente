from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.analysis import AnalysisResult
from services.ia_service import TextSentimentService

analysis_bp = Blueprint("analysis", __name__)
sentiment_service = TextSentimentService()

def _current_user_id():
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return identity


@analysis_bp.post("/analyze-text")
@jwt_required()
def analyze_text():
    payload = request.get_json(force=True) or {}
    source_text = (payload.get("text") or "").strip()
    channel = payload.get("channel", "manual")

    if not source_text:
        return jsonify({"message": "The 'text' field is required."}), HTTPStatus.BAD_REQUEST

    user_id = _current_user_id()

    try:
        ai_result = sentiment_service.analyze(source_text)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), HTTPStatus.BAD_REQUEST

    record = AnalysisResult(
        user_id=user_id,
        source_text=source_text,
        sentiment_label=ai_result.label,
        polarity=ai_result.polarity,
        subjectivity=ai_result.subjectivity,
        summary=ai_result.summary,
        context_data={"channel": channel},
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({"analysis": record.to_dict(), "message": "Text analyzed successfully."})
