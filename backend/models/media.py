from datetime import datetime

from extensions import db


class MediaAnalysis(db.Model):
    __tablename__ = "media_analyses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)
    source_type = db.Column(db.String(20), nullable=False)
    channel = db.Column(db.String(40), nullable=False, default="manual")
    original_filename = db.Column(db.String(255))
    original_path = db.Column(db.String(255), nullable=False)
    snapshot_path = db.Column(db.String(255), nullable=False)
    dominant_emotion = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    detections = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="media_events")
    emotion_counts = db.relationship(
        "MediaEmotionCount",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="MediaEmotionCount.emotion_label",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "media_type": self.media_type,
            "source_type": self.source_type,
            "channel": self.channel,
            "original_filename": self.original_filename,
            "original_path": self.original_path,
            "snapshot_path": self.snapshot_path,
            "dominant_emotion": self.dominant_emotion,
            "confidence": self.confidence,
            "detections": self.detections,
            "emotion_counts": [count.to_dict() for count in self.emotion_counts],
            "created_at": self.created_at.isoformat(),
        }


class MediaEmotionCount(db.Model):
    __tablename__ = "media_emotion_counts"

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(
        db.Integer,
        db.ForeignKey("media_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    emotion_label = db.Column(db.String(20), nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    analysis = db.relationship("MediaAnalysis", back_populates="emotion_counts")

    __table_args__ = (
        db.UniqueConstraint(
            "analysis_id",
            "emotion_label",
            name="uq_media_emotion_counts_analysis_label",
        ),
    )

    def to_dict(self) -> dict:
        return {
            "emotion_label": self.emotion_label,
            "count": self.count,
        }
