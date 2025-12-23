from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
import tempfile
from uuid import uuid4

import cv2
import numpy as np
from flask import Blueprint, abort, current_app, jsonify, request, send_file, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from extensions import db
from models.media import MediaAnalysis, MediaEmotionCount
from services.live_session import LiveSessionManager, LiveSessionError, LiveSessionSummary
from services.media_service import MediaEmotionAnalyzer, MediaStorage

media_bp = Blueprint("media", __name__)
analyzer = MediaEmotionAnalyzer()

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "m4v"}
SOURCE_ALIAS_MAP = {
    "camera": ["webcam", "webcam-live"],
    "image": ["image-upload"],
    "video": ["video-upload"],
}


def _build_storage() -> MediaStorage:
    config = current_app.config
    root = Path(config.get("MEDIA_STORAGE_ROOT")).resolve()
    raw_dir = root / config.get("MEDIA_RAW_SUBDIR", "raw")
    snapshot_dir = root / config.get("MEDIA_SNAPSHOT_SUBDIR", "snapshots")
    return MediaStorage(root_dir=root, raw_dir=raw_dir, snapshot_dir=snapshot_dir)


def _get_live_session_manager() -> LiveSessionManager:
    manager = current_app.extensions.get("live_session_manager")
    if manager is None:
        config = current_app.config
        manager = LiveSessionManager(
            tracked_root=Path(config.get("TRACKED_ROOT")).resolve(),
            emotion_subdir=config.get("SESSION_EMOTION_SUBDIR", "emotion_class"),
            stream_subdir=config.get("SESSION_STREAM_SUBDIR", "session_stream"),
            labels=analyzer.labels,
            snapshot_interval=config.get("SESSION_SNAPSHOT_INTERVAL", 5),
            video_fps=config.get("SESSION_VIDEO_FPS", 12),
        )
        current_app.extensions["live_session_manager"] = manager
    return manager


def _payload_from_request() -> dict:
    if request.is_json:
        return request.get_json(silent=True) or {}
    return {key: request.form.get(key) for key in request.form}


def _decode_image_from_upload(upload) -> np.ndarray:
    upload.stream.seek(0)
    data = upload.read()
    if not data:
        raise ValueError("El fotograma recibido está vacío.")
    array = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
    upload.stream.seek(0)
    if frame is None or frame.size == 0:
        raise ValueError("El fotograma recibido no es una imagen válida.")
    return frame


def _is_allowed(filename: str | None, media_type: str) -> bool:
    if not filename or "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    allowed = ALLOWED_IMAGE_EXTENSIONS if media_type == "image" else ALLOWED_VIDEO_EXTENSIONS
    return extension in allowed


def _current_user_id():
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return identity


def _serialize_record(record: MediaAnalysis) -> dict:
    payload = record.to_dict()
    payload["snapshot_url"] = url_for(
        "media.fetch_media_file", relative_path=record.snapshot_path, _external=False
    )
    payload["original_url"] = url_for(
        "media.fetch_media_file", relative_path=record.original_path, _external=False
    )
    return payload


def _build_emotion_count_entities(counts_payload) -> list[MediaEmotionCount]:
    entities: list[MediaEmotionCount] = []
    if not counts_payload:
        return entities
    for label, qty in (counts_payload or {}).items():
        normalized_label = (label or "").strip()
        if not normalized_label:
            continue
        try:
            qty_value = int(qty)
        except (TypeError, ValueError):
            continue
        entities.append(
            MediaEmotionCount(
                emotion_label=normalized_label,
                count=max(qty_value, 0),
            )
        )
    return entities


def _label_confidence_value(
    label: str,
    confidence_map: dict | None,
    detections: list | None,
    fallback: float | None,
) -> float:
    if confidence_map and label in confidence_map:
        try:
            return float(confidence_map[label])
        except (TypeError, ValueError):
            pass
    label_detections = [
        det
        for det in (detections or [])
        if isinstance(det, dict) and det.get("label") == label
    ]
    if label_detections:
        try:
            return float(
                max(det.get("confidence", 0.0) or 0.0 for det in label_detections)
            )
        except (TypeError, ValueError):
            return float(fallback or 0.0)
    return float(fallback or 0.0)


def _select_face_frame(emotion_faces, label: str, dominant_face, annotated_frame):
    if isinstance(emotion_faces, dict):
        payload = emotion_faces.get(label)
        if isinstance(payload, dict):
            frame = payload.get("face")
        else:
            frame = payload
        if frame is not None and getattr(frame, "size", 0) != 0:
            return frame
    if dominant_face is not None and getattr(dominant_face, "size", 0) != 0:
        return dominant_face
    if annotated_frame is not None and getattr(annotated_frame, "size", 0) != 0:
        return annotated_frame
    return None


def _build_detection_payload(
    label: str,
    count: int,
    total_counts: dict,
    detections: list,
    batch_id: str | None = None,
    extra: dict | None = None,
):
    label_detections = [
        det
        for det in (detections or [])
        if isinstance(det, dict) and det.get("label") == label
    ]
    payload = {
        "counts": {label: count},
        "emotion_label": label,
        "emotion_count": count,
        "total_counts": total_counts,
        "detections": label_detections,
    }
    if batch_id:
        payload["batch_id"] = batch_id
    if extra:
        payload.update(extra)
    return payload


def _persist_live_session_summary(summary: LiveSessionSummary) -> dict | None:
    if summary.frames == 0 or not summary.stream_relative:
        return None

    counts = summary.counts or {}
    if not counts:
        return None

    snapshots = summary.emotion_snapshots or {}
    confidences = summary.emotion_confidences or {}
    records: list[MediaAnalysis] = []
    for label, qty in counts.items():
        try:
            qty_value = int(qty)
        except (TypeError, ValueError):
            continue
        if qty_value <= 0:
            continue
        snapshot_relative = snapshots.get(label) or summary.snapshot_relative
        if not snapshot_relative:
            continue
        detection_payload = _build_detection_payload(
            label,
            qty_value,
            counts,
            [],
            batch_id=summary.session_id,
            extra={
                "session_id": summary.session_id,
                "duration_seconds": summary.duration_seconds,
                "frames": summary.frames,
            },
        )
        record = MediaAnalysis(
            user_id=summary.user_id,
            media_type="video",
            source_type="webcam-live",
            channel=summary.channel,
            original_filename=Path(summary.stream_relative).name,
            original_path=summary.stream_relative,
            snapshot_path=snapshot_relative,
            dominant_emotion=label,
            confidence=_label_confidence_value(
                label,
                confidences,
                [],
                summary.confidence,
            ),
            detections=detection_payload,
        )
        record.emotion_counts = _build_emotion_count_entities({label: qty_value})
        records.append(record)

    if not records:
        return None

    db.session.add_all(records)
    try:
        db.session.commit()
    except Exception as exc:  # pragma: no cover - safeguard
        db.session.rollback()
        current_app.logger.exception("No se pudo guardar la sesión en vivo", exc_info=exc)
        return None

    return [_serialize_record(record) for record in records]


def _process_media_upload(media_type: str, source_type: str, channel: str, upload):
    if upload is None:
        return (
            jsonify({"message": "Se requiere el archivo 'file' en la solicitud."}),
            HTTPStatus.BAD_REQUEST,
        )

    if not _is_allowed(upload.filename, media_type):
        return (
            jsonify({"message": "Formato de archivo no soportado para este tipo de medio."}),
            HTTPStatus.BAD_REQUEST,
        )

    storage = _build_storage()
    raw_path, relative_raw = storage.save_raw(upload, source_type)
    analysis_fn = analyzer.analyze_image if media_type == "image" else analyzer.analyze_video

    try:
        summary = analysis_fn(raw_path)
    except FileNotFoundError as exc:
        raw_path.unlink(missing_ok=True)
        current_app.logger.exception("Modelo o recursos no encontrados", exc_info=exc)
        return (
            jsonify({"message": "Modelo de emociones no disponible. Verifique los archivos en 'tracked/'."}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    except ValueError as exc:
        raw_path.unlink(missing_ok=True)
        return jsonify({"message": str(exc)}), HTTPStatus.BAD_REQUEST
    except Exception as exc:  # pragma: no cover - safeguard
        raw_path.unlink(missing_ok=True)
        current_app.logger.exception("Falla inesperada al analizar multimedia", exc_info=exc)
        return jsonify({"message": "Error interno al procesar el archivo."}), HTTPStatus.INTERNAL_SERVER_ERROR

    dominant_face = summary.pop("dominant_face", None)
    annotated_frame = summary.pop("annotated_frame", None)
    emotion_faces = summary.pop("emotion_faces", {}) or {}
    confidence_map = summary.get("emotion_confidences") or {}
    summary_counts = dict(summary.get("counts") or {})
    if not summary_counts:
        raw_path.unlink(missing_ok=True)
        return (
            jsonify({"message": "No se detectaron emociones válidas en el archivo proporcionado."}),
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    saved_snapshots: list[Path] = []
    created_records: list[MediaAnalysis] = []
    detections = summary.get("detections") or []
    batch_id = uuid4().hex
    user_id = _current_user_id()

    try:
        for label, qty in summary_counts.items():
            try:
                qty_value = int(qty)
            except (TypeError, ValueError):
                continue
            if qty_value <= 0:
                continue
            face_frame = _select_face_frame(emotion_faces, label, dominant_face, annotated_frame)
            if face_frame is None or getattr(face_frame, "size", 0) == 0:
                raise ValueError(f"No se pudo generar una captura representativa para la emoción {label}.")

            snapshot_path, relative_snapshot = storage.save_snapshot(
                face_frame,
                label,
                source_type,
            )
            saved_snapshots.append(snapshot_path)

            label_confidence = _label_confidence_value(
                label,
                confidence_map,
                detections,
                summary.get("confidence"),
            )
            detection_payload = _build_detection_payload(
                label,
                qty_value,
                summary_counts,
                detections,
                batch_id=batch_id,
                extra={"media_type": media_type, "source_type": source_type},
            )
            record = MediaAnalysis(
                user_id=user_id,
                media_type=media_type,
                source_type=source_type,
                channel=channel or "manual",
                original_filename=upload.filename,
                original_path=relative_raw,
                snapshot_path=relative_snapshot,
                dominant_emotion=label,
                confidence=label_confidence,
                detections=detection_payload,
            )
            record.emotion_counts = _build_emotion_count_entities({label: qty_value})
            created_records.append(record)
    except ValueError as exc:
        raw_path.unlink(missing_ok=True)
        for snapshot_file in saved_snapshots:
            snapshot_file.unlink(missing_ok=True)
        return jsonify({"message": str(exc)}), HTTPStatus.UNPROCESSABLE_ENTITY

    if not created_records:
        raw_path.unlink(missing_ok=True)
        for snapshot_file in saved_snapshots:
            snapshot_file.unlink(missing_ok=True)
        return (
            jsonify({"message": "No se generaron registros de emociones válidos."}),
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    db.session.add_all(created_records)
    try:
        db.session.commit()
    except Exception as exc:  # pragma: no cover - safeguard
        db.session.rollback()
        current_app.logger.exception("No se pudo guardar el análisis multimedia", exc_info=exc)
        for snapshot_file in saved_snapshots:
            snapshot_file.unlink(missing_ok=True)
        return (
            jsonify({"message": "No se pudo guardar el resultado en la base de datos."}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    serialized = [_serialize_record(record) for record in created_records]
    payload = {
        "analyses": serialized,
        "message": "Análisis multimedia completado.",
    }
    if serialized:
        payload["analysis"] = serialized[0]

    return jsonify(payload), HTTPStatus.CREATED


def _analyze_preview_media(media_type: str, upload):
    if upload is None:
        return (
            jsonify({"message": "Se requiere el archivo 'file' en la solicitud."}),
            HTTPStatus.BAD_REQUEST,
        )

    if media_type == "image":
        frame = _decode_image_from_upload(upload)
        summary = analyzer.analyze_array(frame)
        return summary, frame

    suffix = ".mp4"
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_name = tmp_file.name
    tmp_file.close()
    upload.save(temp_name)
    temp_path = Path(temp_name)

    try:
        summary = analyzer.analyze_video(temp_path, max_frames=90, sample_rate=6)
    finally:
        temp_path.unlink(missing_ok=True)

    return summary, None


@media_bp.get("/media/model-metadata")
@jwt_required(optional=True)
def model_metadata():
    metadata = analyzer.model_metadata()
    metadata["storage_root"] = current_app.config.get("MEDIA_STORAGE_ROOT")
    metadata["raw_subdir"] = current_app.config.get("MEDIA_RAW_SUBDIR")
    metadata["snapshot_subdir"] = current_app.config.get("MEDIA_SNAPSHOT_SUBDIR")
    return jsonify(metadata)


@media_bp.post("/media/analyze")
@jwt_required()
def analyze_media():
    payload = _payload_from_request()
    media_type = (payload.get("media_type") or "image").lower()
    if media_type not in {"image", "video"}:
        return jsonify({"message": "El parámetro 'media_type' debe ser 'image' o 'video'."}), HTTPStatus.BAD_REQUEST

    source_type = (payload.get("source_type") or "upload").lower()
    channel = payload.get("channel", "manual")

    upload = request.files.get("file")
    return _process_media_upload(media_type, source_type, channel, upload)


@media_bp.post("/analyze-imagen")
@jwt_required()
def analyze_image_upload():
    channel = request.form.get("channel", "manual")
    upload = request.files.get("file")
    return _process_media_upload("image", "image-upload", channel, upload)


@media_bp.post("/analyze-image")
@jwt_required()
def analyze_image_upload_alias():
    """English alias that mirrors /analyze-imagen for compatibility."""
    return analyze_image_upload()


@media_bp.post("/analyze-video")
@jwt_required()
def analyze_video_upload():
    channel = request.form.get("channel", "manual")
    upload = request.files.get("file")
    return _process_media_upload("video", "video-upload", channel, upload)


@media_bp.post("/analyze-webcam")
@jwt_required()
def analyze_webcam_capture():
    channel = request.form.get("channel", "webcam")
    upload = request.files.get("file")
    return _process_media_upload("video", "webcam", channel, upload)


@media_bp.post("/media/live-session/start")
@jwt_required()
def start_live_session():
    payload = request.get_json(silent=True) or {}
    channel = (payload.get("channel") or "webcam-live").strip() or "webcam-live"
    manager = _get_live_session_manager()
    session = manager.start_session(user_id=_current_user_id(), channel=channel)
    return jsonify({"session_id": session.session_id, "channel": session.channel})


@media_bp.post("/media/live-session/stop")
@jwt_required()
def stop_live_session():
    payload = request.get_json(silent=True) or {}
    session_id = (payload.get("session_id") or "").strip()
    if not session_id:
        return jsonify({"message": "Proporciona el identificador de la sesión."}), HTTPStatus.BAD_REQUEST

    manager = _get_live_session_manager()
    try:
        summary = manager.stop_session(session_id)
    except LiveSessionError as exc:
        return jsonify({"message": str(exc)}), HTTPStatus.NOT_FOUND

    records = _persist_live_session_summary(summary) or []
    response = {
        "session_id": summary.session_id,
        "counts": summary.counts,
        "dominant_emotion": summary.dominant_emotion,
        "confidence": summary.confidence,
        "duration_seconds": summary.duration_seconds,
        "frames": summary.frames,
        "snapshot_path": summary.snapshot_relative,
        "stream_path": summary.stream_relative,
        "analyses": records,
    }
    if records:
        response["analysis"] = records[0]
    return jsonify(response)


@media_bp.post("/analyze-webcam-frame")
@jwt_required()
def analyze_webcam_frame():
    upload = request.files.get("file")
    if upload is None:
        return jsonify({"message": "Se requiere el archivo 'file' en la solicitud."}), HTTPStatus.BAD_REQUEST

    if not upload.filename:
        upload.filename = f"webcam-frame-{uuid4().hex}.jpg"

    if not _is_allowed(upload.filename, "image"):
        return (
            jsonify({"message": "El fotograma debe ser una imagen válida (jpg/png)."}),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        summary, raw_frame = _analyze_preview_media("image", upload)
    except FileNotFoundError as exc:
        current_app.logger.exception("Modelo no disponible para vista previa", exc_info=exc)
        return (
            jsonify({"message": "Modelo de emociones no disponible para vista previa."}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    except ValueError as exc:
        return jsonify({"message": str(exc)}), HTTPStatus.BAD_REQUEST
    except cv2.error as exc:
        current_app.logger.exception("OpenCV error en vista previa de webcam", exc_info=exc)
        return (
            jsonify({"message": "La cámara envió un fotograma incompatible. Intenta reducir la resolución."}),
            HTTPStatus.BAD_REQUEST,
        )
    except Exception as exc:  # pragma: no cover
        current_app.logger.exception("Error en vista previa de webcam", exc_info=exc)
        return jsonify({"message": "No se pudo analizar el fotograma."}), HTTPStatus.INTERNAL_SERVER_ERROR

    session_id = (request.form.get("session_id") or "").strip()
    session_payload = None
    annotated_frame = summary.get("annotated_frame")
    if session_id and raw_frame is not None:
        manager = _get_live_session_manager()
        try:
            session_payload = manager.process_frame(
                session_id,
                raw_frame,
                summary,
                annotated_frame,
                summary.get("dominant_face"),
                summary.get("emotion_faces"),
            )
        except LiveSessionError as exc:
            return jsonify({"message": str(exc)}), HTTPStatus.BAD_REQUEST

    summary.pop("annotated_frame", None)
    summary.pop("dominant_face", None)
    summary.pop("emotion_faces", None)
    summary.pop("emotion_confidences", None)
    payload = {
        "dominant_emotion": summary["dominant_emotion"],
        "confidence": summary["confidence"],
        "counts": summary.get("counts", {}),
        "detections": summary.get("detections", []),
    }
    if session_payload:
        payload["session"] = session_payload
    return jsonify(payload)


@media_bp.get("/media/records")
@jwt_required()
def list_media_records():
    user_id = _current_user_id()
    try:
        limit = int(request.args.get("limit", 25))
    except ValueError:
        return jsonify({"message": "El parámetro 'limit' debe ser numérico."}), HTTPStatus.BAD_REQUEST

    limit = max(1, min(limit, 100))
    media_type = (request.args.get("media_type") or "").strip().lower()
    source_type = (request.args.get("source_type") or "").strip().lower()
    emotion = (request.args.get("emotion") or "").strip()

    def _apply_source_filter(query_obj, value):
        aliases = SOURCE_ALIAS_MAP.get(value)
        if not aliases:
            return query_obj.filter(MediaAnalysis.source_type == value)
        if len(aliases) == 1:
            return query_obj.filter(MediaAnalysis.source_type == aliases[0])
        return query_obj.filter(MediaAnalysis.source_type.in_(aliases))

    query = MediaAnalysis.query.filter_by(user_id=user_id)
    if media_type and media_type != "all":
        query = query.filter(MediaAnalysis.media_type == media_type)
    if source_type and source_type != "all":
        query = _apply_source_filter(query, source_type)
    if emotion:
        query = query.filter(MediaAnalysis.dominant_emotion.ilike(emotion))

    records = query.order_by(MediaAnalysis.created_at.desc()).limit(limit).all()

    emotion_query = MediaAnalysis.query.filter_by(user_id=user_id)
    if media_type and media_type != "all":
        emotion_query = emotion_query.filter(MediaAnalysis.media_type == media_type)
    if source_type and source_type != "all":
        emotion_query = _apply_source_filter(emotion_query, source_type)
    available_emotions = sorted(
        {
            value
            for (value,) in emotion_query.with_entities(MediaAnalysis.dominant_emotion).distinct().all()
            if value
        }
    )

    source_query = MediaAnalysis.query.filter_by(user_id=user_id)
    if media_type and media_type != "all":
        source_query = source_query.filter(MediaAnalysis.media_type == media_type)
    available_sources = sorted(
        {
            value
            for (value,) in source_query.with_entities(MediaAnalysis.source_type).distinct().all()
            if value
        }
    )

    payload = {
        "items": [_serialize_record(record) for record in records],
        "filters": {
            "media_type": media_type or None,
            "source_type": source_type or None,
            "emotion": emotion or None,
            "available_emotions": available_emotions,
            "available_sources": available_sources,
        },
    }
    return jsonify(payload)


@media_bp.get("/media/files/<path:relative_path>")
@jwt_required()
def fetch_media_file(relative_path: str):
    user_id = _current_user_id()
    record = (
        MediaAnalysis.query.filter_by(user_id=user_id)
        .filter(
            or_(
                MediaAnalysis.snapshot_path == relative_path,
                MediaAnalysis.original_path == relative_path,
            )
        )
        .first()
    )
    if record is None:
        abort(404)

    storage = _build_storage()
    tracked_root = Path(current_app.config.get("TRACKED_ROOT")).resolve()
    candidate_roots = [storage.root_dir, tracked_root]

    for root in candidate_roots:
        target_path = (root / relative_path).resolve()
        if not target_path.exists():
            continue
        if root not in target_path.parents and target_path != root:
            continue
        return send_file(target_path)

    abort(404)
