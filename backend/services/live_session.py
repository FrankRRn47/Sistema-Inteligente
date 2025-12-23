from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, Optional
from uuid import uuid4
import time

import cv2
import numpy as np


class LiveSessionError(RuntimeError):
    """Raised when a requested live session is not available."""


@dataclass
class LiveSessionSummary:
    session_id: str
    user_id: int
    channel: str
    counts: Dict[str, int]
    dominant_emotion: Optional[str]
    confidence: Optional[float]
    snapshot_relative: Optional[str]
    stream_relative: Optional[str]
    duration_seconds: float
    frames: int
    started_at: datetime
    finished_at: datetime
    emotion_snapshots: Dict[str, str] = field(default_factory=dict)
    emotion_confidences: Dict[str, float] = field(default_factory=dict)


class LiveSession:
    def __init__(
        self,
        *,
        user_id: int,
        channel: str,
        tracked_root: Path,
        emotion_subdir: str,
        stream_subdir: str,
        labels: list[str],
        snapshot_interval: int,
        video_fps: int,
    ) -> None:
        self.session_id = uuid4().hex
        self.user_id = user_id
        self.channel = channel
        self.started_at = datetime.utcnow()
        self.finished_at: Optional[datetime] = None

        self.tracked_root = tracked_root
        self.emotion_root = tracked_root / emotion_subdir
        self.stream_root = tracked_root / stream_subdir
        self.emotion_root.mkdir(parents=True, exist_ok=True)
        self.stream_root.mkdir(parents=True, exist_ok=True)
        for label in labels:
            (self.emotion_root / label.lower()).mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.stream_path = self.stream_root / f"session_{timestamp}_{self.session_id}.mp4"
        self.snapshot_interval = snapshot_interval
        self.video_fps = max(1, video_fps)

        self._counts: Counter[str] = Counter()
        self._last_snapshot_ts = 0.0
        self._last_snapshot_path: Optional[Path] = None
        self._label_snapshots: Dict[str, Path] = {}
        self._video_writer: Optional[cv2.VideoWriter] = None
        self._frame_size: Optional[tuple[int, int]] = None
        self._frames = 0
        self._latest_confidence: Optional[float] = None
        self._latest_dominant: Optional[str] = None
        self._latest_snapshot_frame: Optional[np.ndarray] = None
        self._last_face_by_label: Dict[str, np.ndarray] = {}
        self._emotion_best_confidences: Dict[str, float] = {}

    def _ensure_writer(self, frame: np.ndarray) -> None:
        if self._video_writer is not None:
            return
        height, width = frame.shape[:2]
        self._frame_size = (width, height)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._video_writer = cv2.VideoWriter(str(self.stream_path), fourcc, self.video_fps, (width, height))

    def _relative_path(self, path: Optional[Path]) -> Optional[str]:
        if path is None:
            return None
        try:
            return path.relative_to(self.tracked_root).as_posix()
        except ValueError:
            return path.as_posix()

    def ingest(
        self,
        frame: np.ndarray,
        summary: Dict,
        annotated_frame: Optional[np.ndarray],
        face_frame: Optional[np.ndarray] = None,
        emotion_faces: Optional[Dict[str, Dict[str, object]]] = None,
    ) -> Dict:
        self._ensure_writer(frame)
        self._video_writer.write(frame)
        self._frames += 1

        counts = Counter(summary.get("counts") or {})
        self._counts.update(counts)
        self._latest_dominant = summary.get("dominant_emotion") or self._latest_dominant
        self._latest_confidence = summary.get("confidence") or self._latest_confidence
        if face_frame is not None and face_frame.size != 0:
            self._latest_snapshot_frame = face_frame
        elif annotated_frame is not None:
            self._latest_snapshot_frame = annotated_frame
        else:
            self._latest_snapshot_frame = frame

        for label, conf in (summary.get("emotion_confidences") or {}).items():
            self._emotion_best_confidences[label] = max(
                conf,
                self._emotion_best_confidences.get(label, 0.0),
            )

        if emotion_faces:
            for label, payload in emotion_faces.items():
                face_payload = payload.get("face") if isinstance(payload, dict) else None
                if face_payload is not None and getattr(face_payload, "size", 0) != 0:
                    self._last_face_by_label[label] = face_payload

        now = time.time()
        should_capture = now - self._last_snapshot_ts >= self.snapshot_interval
        if should_capture and emotion_faces:
            any_saved = False
            for label, payload in emotion_faces.items():
                face_payload = payload.get("face") if isinstance(payload, dict) else None
                if face_payload is None or getattr(face_payload, "size", 0) == 0:
                    continue
                destination = self._save_snapshot(label, face_payload, suffix=int(now))
                self._label_snapshots[label] = destination
                if label == self._latest_dominant:
                    self._last_snapshot_path = destination
                any_saved = True
            if any_saved:
                self._last_snapshot_ts = now
        elif should_capture and self._latest_dominant and self._latest_snapshot_frame is not None:
            destination = self._save_snapshot(self._latest_dominant, self._latest_snapshot_frame, suffix=int(now))
            self._label_snapshots[self._latest_dominant] = destination
            self._last_snapshot_path = destination
            self._last_snapshot_ts = now

        return {
            "session_id": self.session_id,
            "counts": dict(self._counts),
            "frames": self._frames,
            "dominant_emotion": self._latest_dominant,
            "confidence": self._latest_confidence,
            "snapshot_path": self._relative_path(self._last_snapshot_path),
        }

    def _save_snapshot(self, label: str, frame: np.ndarray, suffix: Optional[object] = None) -> Path:
        label_slug = (label or "otros").strip().lower().replace(" ", "-") or "otros"
        label_dir = self.emotion_root / label_slug
        label_dir.mkdir(parents=True, exist_ok=True)
        timestamp = suffix if suffix is not None else int(time.time())
        filename = f"{label_slug}_{self.session_id}_{timestamp}.jpg"
        destination = label_dir / filename
        cv2.imwrite(str(destination), frame)
        return destination

    def stop(self) -> LiveSessionSummary:
        if self._video_writer is not None:
            self._video_writer.release()
            self._video_writer = None
        if self._latest_snapshot_frame is not None and self._latest_dominant:
            if self._latest_dominant not in self._label_snapshots:
                destination = self._save_snapshot(self._latest_dominant, self._latest_snapshot_frame, suffix="final")
                self._label_snapshots[self._latest_dominant] = destination
            if self._last_snapshot_path is None:
                self._last_snapshot_path = self._label_snapshots[self._latest_dominant]
        for label, face in list(self._last_face_by_label.items()):
            if label in self._label_snapshots:
                continue
            if face is None or getattr(face, "size", 0) == 0:
                continue
            self._label_snapshots[label] = self._save_snapshot(label, face, suffix="final")
        self.finished_at = datetime.utcnow()
        duration = (self.finished_at - self.started_at).total_seconds()
        dominant, dominant_count = (None, 0)
        if self._counts:
            dominant, dominant_count = self._counts.most_common(1)[0]
        emotion_snapshot_map = {
            label: self._relative_path(path)
            for label, path in self._label_snapshots.items()
            if path is not None
        }
        return LiveSessionSummary(
            session_id=self.session_id,
            user_id=self.user_id,
            channel=self.channel,
            counts=dict(self._counts),
            dominant_emotion=dominant,
            confidence=self._latest_confidence,
            snapshot_relative=self._relative_path(self._last_snapshot_path),
            stream_relative=self._relative_path(self.stream_path if self._frames else None),
            duration_seconds=duration,
            frames=self._frames,
            started_at=self.started_at,
            finished_at=self.finished_at,
            emotion_snapshots={k: v for k, v in emotion_snapshot_map.items() if v},
            emotion_confidences=dict(self._emotion_best_confidences),
        )


class LiveSessionManager:
    def __init__(
        self,
        *,
        tracked_root: Path,
        emotion_subdir: str,
        stream_subdir: str,
        labels: list[str],
        snapshot_interval: int,
        video_fps: int,
    ) -> None:
        self._tracked_root = tracked_root
        self._emotion_subdir = emotion_subdir
        self._stream_subdir = stream_subdir
        self._labels = labels
        self._snapshot_interval = snapshot_interval
        self._video_fps = video_fps
        self._sessions: Dict[str, LiveSession] = {}
        self._lock = Lock()

    def start_session(self, user_id: int, channel: str) -> LiveSession:
        session = LiveSession(
            user_id=user_id,
            channel=channel,
            tracked_root=self._tracked_root,
            emotion_subdir=self._emotion_subdir,
            stream_subdir=self._stream_subdir,
            labels=self._labels,
            snapshot_interval=self._snapshot_interval,
            video_fps=self._video_fps,
        )
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def _get_session(self, session_id: str) -> LiveSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if not session:
            raise LiveSessionError("Sesión en vivo no encontrada o finalizada.")
        return session

    def process_frame(
        self,
        session_id: str,
        frame: np.ndarray,
        summary: Dict,
        annotated_frame: Optional[np.ndarray],
        face_frame: Optional[np.ndarray] = None,
        emotion_faces: Optional[Dict[str, Dict[str, object]]] = None,
    ) -> Dict:
        session = self._get_session(session_id)
        payload_faces = emotion_faces if emotion_faces is not None else summary.get("emotion_faces")
        return session.ingest(frame, summary, annotated_frame, face_frame, payload_faces)

    def stop_session(self, session_id: str) -> LiveSessionSummary:
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session is None:
            raise LiveSessionError("Sesión en vivo no encontrada o ya cerrada.")
        return session.stop()

    def has_session(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._sessions
