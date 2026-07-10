from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import TranslationFeedback


class TranslationFeedbackRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_feedback(
        self,
        *,
        source_text: str,
        model_translation: str,
        user_corrected_translation: str,
        job_id: int | None = None,
        chunk_id: int | None = None,
        rating: int | None = None,
        feedback_type: str | None = None,
        comment: str | None = None,
    ) -> TranslationFeedback:
        feedback = TranslationFeedback(
            job_id=job_id,
            chunk_id=chunk_id,
            source_text=source_text,
            model_translation=model_translation,
            user_corrected_translation=user_corrected_translation,
            rating=rating,
            feedback_type=feedback_type,
            comment=comment,
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
