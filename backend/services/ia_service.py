from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import List, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


@dataclass
class SentimentPayload:
    label: str
    polarity: float
    subjectivity: float
    summary: str


TRAINING_DATA: Sequence[tuple[str, str]] = (
    # Positive
    ("Me encantó la experiencia del servicio y volveré pronto", "positive"),
    ("El producto superó mis expectativas, es fantástico", "positive"),
    ("Excelente atención al cliente, resolvieron todo rápido", "positive"),
    ("La reunión fue muy productiva y salimos motivados", "positive"),
    ("They delivered ahead of schedule with great quality", "positive"),
    ("La aplicación es intuitiva y cómoda de usar", "positive"),
    ("Great vibes from the team, everyone was helpful", "positive"),
    # Neutral
    ("La reunión se limitó a revisar métricas sin decisiones", "neutral"),
    ("El correo solo confirma que seguimos en la misma etapa", "neutral"),
    ("Se comparte el acta del comité, favor de leerla", "neutral"),
    ("The shipment is in transit and arrives on Monday", "neutral"),
    ("No hubo novedades relevantes en el evento", "neutral"),
    ("Informe semanal adjunto para su referencia", "neutral"),
    ("Agenda actualizada con los mismos puntos", "neutral"),
    # Negative
    ("El servicio fue terrible y nadie respondió mis dudas", "negative"),
    ("Estamos frustrados por los constantes retrasos", "negative"),
    ("Terrible quality, necesitamos un reembolso inmediato", "negative"),
    ("La experiencia dejó una sensación amarga en el equipo", "negative"),
    ("El cliente está molesto por los errores repetidos", "negative"),
    ("Nos sentimos ignorados durante toda la sesión", "negative"),
    ("The worst support interaction we have had so far", "negative"),
)


class TextSentimentService:
    """Sentiment classifier powered by a compact scikit-learn pipeline."""

    def __init__(self) -> None:
        self._pipeline: Pipeline | None = None
        self._lock = threading.Lock()

    def analyze(self, text: str) -> SentimentPayload:
        if not text or not text.strip():
            raise ValueError("Input text is required for analysis.")

        pipeline = self._ensure_model()
        prediction = pipeline.predict([text])[0]
        probabilities = pipeline.predict_proba([text])[0]
        classes: List[str] = list(pipeline.classes_)
        score_lookup = {label: prob for label, prob in zip(classes, probabilities)}

        positive_score = score_lookup.get("positive", 0.0)
        negative_score = score_lookup.get("negative", 0.0)
        neutral_score = score_lookup.get("neutral", 0.0)

        polarity = round(positive_score - negative_score, 4)
        subjectivity = round(1.0 - neutral_score, 4)
        summary = self._build_summary(text, prediction, positive_score, negative_score)
        return SentimentPayload(prediction, polarity, subjectivity, summary)

    def _ensure_model(self) -> Pipeline:
        if self._pipeline is not None:
            return self._pipeline
        with self._lock:
            if self._pipeline is None:
                texts = [sample for sample, _ in TRAINING_DATA]
                labels = [label for _, label in TRAINING_DATA]
                self._pipeline = Pipeline(
                    steps=[
                        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
                        ("clf", LogisticRegression(max_iter=400, multi_class="auto")),
                    ]
                )
                self._pipeline.fit(texts, labels)
        return self._pipeline

    def _build_summary(self, text: str, label: str, pos_score: float, neg_score: float) -> str:
        snippet = (text.strip().splitlines() or [""])[0][:180].strip()
        confidence = max(pos_score, neg_score)
        return (
            f"{label.title()} sentiment ({confidence:.2%} confidence): {snippet}"
            if snippet
            else f"{label.title()} sentiment detected."
        )
