from datetime import datetime

from extensions import db


class AnalysisResult(db.Model):
    __tablename__ = "analysis_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    source_text = db.Column(db.Text, nullable=False)
    sentiment_label = db.Column(db.String(20), nullable=False)
    polarity = db.Column(db.Float, nullable=False)
    subjectivity = db.Column(db.Float, nullable=False)
    summary = db.Column(db.String(255))
    context_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="analyses")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sentiment_label": self.sentiment_label,
            "polarity": self.polarity,
            "subjectivity": self.subjectivity,
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
            "context_data": self.context_data,
        }
