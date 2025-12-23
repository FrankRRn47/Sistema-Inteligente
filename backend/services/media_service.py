from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
from uuid import uuid4

import cv2
import numpy as np
from tensorflow.keras.models import load_model
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class MediaEmotionAnalyzer:
    """Loads the CNN model and performs emotion detection on images or videos."""

    def __init__(self) -> None:
        self._model = None
        self._backend_dir = Path(__file__).resolve().parents[1]
        self._repo_root = self._backend_dir.parent
        self._weights_path = self._repo_root / "tracked" / "model_weights.h5"
        self._cascade_path = self._repo_root / "tracked" / "haarcascade_frontalface_default.xml"
        self._face_detector = cv2.CascadeClassifier(str(self._cascade_path))
        self._emotion_labels = [
            "Angry",
            "Disgust",
            "Fear",
            "Happy",
            "Neutral",
            "Sad",
            "Surprise",
        ]

    def analyze_image(self, image_path: Path) -> Dict:
        frame = cv2.imread(str(image_path))
        if frame is None:
            raise ValueError("No se pudo leer la imagen proporcionada.")
        summary, annotated = self._analyze_frame(frame)
        summary["annotated_frame"] = annotated
        return summary

    def analyze_array(self, frame) -> Dict:
        if frame is None or getattr(frame, "size", 0) == 0:
            raise ValueError("El fotograma recibido está vacío o es inválido.")
        summary, annotated = self._analyze_frame(frame)
        summary["annotated_frame"] = annotated
        return summary

    def analyze_video(self, video_path: Path, max_frames: int = 180, sample_rate: int = 6) -> Dict:
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise ValueError("No se pudo procesar el video proporcionado.")

        summaries: List[Dict] = []
        frame_index = 0
        while frame_index < max_frames:
            grabbed, frame = capture.read()
            if not grabbed:
                break
            if frame_index % sample_rate == 0:
                try:
                    summary, annotated = self._analyze_frame(frame)
                except ValueError:
                    frame_index += 1
                    continue
                summary["annotated_frame"] = annotated
                summaries.append(summary)
            frame_index += 1

        capture.release()

        if not summaries:
            raise ValueError("No se detectaron rostros en el video.")

        return self._combine_summaries(summaries)

    def model_metadata(self) -> Dict:
        return {
            "labels": self._emotion_labels,
            "weights_path": str(self._weights_path.name),
            "has_model": self._weights_path.exists(),
        }

    @property
    def labels(self) -> List[str]:
        return list(self._emotion_labels)

    # ------------------------------------------------------------------
    def _load_model(self):
        if self._model is None:
            if not self._weights_path.exists():
                raise FileNotFoundError(
                    "No se encontró el archivo de pesos del modelo en tracked/model_weights.h5"
                )
            self._model = load_model(self._weights_path)
        return self._model

    def _analyze_frame(self, frame) -> Tuple[Dict, np.ndarray]:
        grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._face_detector.detectMultiScale(grayscale, 1.3, 5)
        if len(faces) == 0:
            raise ValueError("No se detectaron rostros en la imagen proporcionada.")

        annotated = frame.copy()
        detections = []
        emotion_faces: Dict[str, Dict[str, object]] = {}
        height, width = frame.shape[:2]
        model = self._load_model()

        for (x, y, w, h) in faces:
            roi_gray = grayscale[y : y + h, x : x + w]
            roi_gray = cv2.resize(roi_gray, (48, 48))
            roi = roi_gray.reshape(1, 48, 48, 1) / 255.0
            prediction = model.predict(roi, verbose=0)[0]
            index = int(np.argmax(prediction))
            label = self._emotion_labels[index]
            confidence = float(prediction[index])

            detections.append(
                {
                    "label": label,
                    "confidence": round(confidence, 4),
                    "box": [int(x), int(y), int(w), int(h)],
                }
            )

            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 0), 2)
            cv2.putText(
                annotated,
                f"{label} {confidence:.2f}",
                (x, max(20, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 0),
                2,
                cv2.LINE_AA,
            )

            x1 = max(int(x), 0)
            y1 = max(int(y), 0)
            x2 = min(int(x + w), width)
            y2 = min(int(y + h), height)
            if x2 > x1 and y2 > y1:
                face_crop = frame[y1:y2, x1:x2].copy()
                if face_crop.size != 0:
                    current = emotion_faces.get(label)
                    if current is None or confidence > current.get("confidence", 0.0):
                        emotion_faces[label] = {
                            "face": face_crop,
                            "confidence": float(confidence),
                        }

        summary = self._build_summary(detections)
        formatted_faces = {}
        for label, payload in emotion_faces.items():
            formatted_faces[label] = {
                "face": payload["face"],
                "confidence": round(float(payload.get("confidence", 0.0)), 4),
            }
        summary["emotion_faces"] = formatted_faces
        summary.setdefault("emotion_confidences", {})
        for label, payload in formatted_faces.items():
            current = summary["emotion_confidences"].get(label, 0.0)
            if payload["confidence"] > current:
                summary["emotion_confidences"][label] = payload["confidence"]

        dominant_face = None
        dominant_label = summary.get("dominant_emotion")
        if dominant_label and dominant_label in formatted_faces:
            dominant_face = formatted_faces[dominant_label]["face"]
        if dominant_face is not None:
            summary["dominant_face"] = dominant_face
        return summary, annotated

    def _build_summary(self, detections: List[Dict]) -> Dict:
        counts = Counter(det["label"] for det in detections)
        dominant = counts.most_common(1)[0]
        dominant_label = dominant[0]
        per_label_confidences: Dict[str, float] = {}
        for det in detections:
            label = det["label"]
            per_label_confidences[label] = max(per_label_confidences.get(label, 0.0), det["confidence"])
        confidence = per_label_confidences.get(dominant_label, 0.0)
        return {
            "dominant_emotion": dominant_label,
            "confidence": round(confidence, 4),
            "counts": dict(counts),
            "detections": detections,
            "emotion_confidences": {label: round(conf, 4) for label, conf in per_label_confidences.items()},
        }

    def _combine_summaries(self, summaries: List[Dict]) -> Dict:
        combined_counts = Counter()
        best_frame = summaries[0]
        combined_faces: Dict[str, Dict[str, object]] = {}
        combined_confidences: Dict[str, float] = {}
        for summary in summaries:
            combined_counts.update(summary["counts"])
            if summary["confidence"] > best_frame["confidence"]:
                best_frame = summary
            for label, payload in (summary.get("emotion_faces") or {}).items():
                existing = combined_faces.get(label)
                payload_conf = float(payload.get("confidence", 0.0))
                if existing is None or payload_conf > float(existing.get("confidence", 0.0)):
                    combined_faces[label] = payload
            for label, conf in (summary.get("emotion_confidences") or {}).items():
                combined_confidences[label] = max(conf, combined_confidences.get(label, 0.0))

        dominant = combined_counts.most_common(1)[0]
        dominant_face = None
        if combined_faces and dominant[0] in combined_faces:
            dominant_face = combined_faces[dominant[0]].get("face")
        return {
            "dominant_emotion": dominant[0],
            "confidence": best_frame["confidence"],
            "counts": dict(combined_counts),
            "detections": best_frame["detections"],
            "annotated_frame": best_frame["annotated_frame"],
            "dominant_face": dominant_face if dominant_face is not None else best_frame.get("dominant_face"),
            "emotion_faces": combined_faces,
            "emotion_confidences": combined_confidences or best_frame.get("emotion_confidences", {}),
        }


@dataclass
class MediaStorage:
    root_dir: Path
    raw_dir: Path
    snapshot_dir: Path

    def __post_init__(self):
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_category(self, category: str | None) -> str:
        if not category:
            return "otros"
        normalized = category.strip().lower().replace(" ", "-")
        cleaned = ''.join(ch if ch.isalnum() or ch in {'-', '_'} else '-' for ch in normalized)
        while '--' in cleaned:
            cleaned = cleaned.replace('--', '-')
        return cleaned or "otros"

    def _category_dir(self, base: Path, category: str | None) -> Path:
        bucket = self._normalize_category(category)
        path = base / bucket
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _prepare_snapshot(self, frame, size: int = 320):
        if frame is None or getattr(frame, "size", 0) == 0:
            raise ValueError("No se recibió una captura válida para almacenar.")
        prepared = frame
        if len(prepared.shape) == 2 or (prepared.shape[-1] == 1):
            prepared = cv2.cvtColor(prepared, cv2.COLOR_GRAY2BGR)
        height, width = prepared.shape[:2]
        side = min(height, width)
        if side <= 0:
            raise ValueError("La captura generada está vacía o dañada.")
        y_start = max((height - side) // 2, 0)
        x_start = max((width - side) // 2, 0)
        cropped = prepared[y_start : y_start + side, x_start : x_start + side]
        resized = cv2.resize(cropped, (size, size))
        return resized

    def save_raw(self, file_storage: FileStorage, source_bucket: str | None) -> Tuple[Path, str]:
        filename = secure_filename(file_storage.filename or f"media_{uuid4().hex}")
        final_name = f"{int(time.time())}_{filename}"
        destination_dir = self._category_dir(self.raw_dir, source_bucket)
        destination = destination_dir / final_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        file_storage.save(destination)
        relative = destination.relative_to(self.root_dir).as_posix()
        return destination, relative

    def save_snapshot(self, frame, dominant_label: str, source_bucket: str | None) -> Tuple[Path, str]:
        snapshot_frame = self._prepare_snapshot(frame)
        snapshot_name = f"snapshot_{dominant_label.lower()}_{uuid4().hex}.jpg"
        destination_dir = self._category_dir(self.snapshot_dir, source_bucket)
        destination = destination_dir / snapshot_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        success = cv2.imwrite(str(destination), snapshot_frame)
        if not success:
            raise ValueError("No se pudo guardar la captura procesada del análisis.")
        relative = destination.relative_to(self.root_dir).as_posix()
        return destination, relative
