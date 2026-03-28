from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.recommendation import Recommendation


class VisualizationJob(Base):
    __tablename__ = "visualization_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    recommendation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)

    # Job state
    status: Mapped[str] = mapped_column(
        String(20), default="queued"
    )  # queued, processing, completed, failed

    # Input payload sent to SD worker
    input_payload: Mapped[Optional[dict]] = mapped_column(JSON)

    # Output
    image_url: Mapped[Optional[str]] = mapped_column(Text)  # S3 URL (expires in 24h)
    image_s3_key: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Prompt used
    positive_prompt: Mapped[Optional[str]] = mapped_column(Text)
    negative_prompt: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    recommendation: Mapped[Optional["Recommendation"]] = relationship(
        "Recommendation", back_populates="visualization_jobs"
    )
