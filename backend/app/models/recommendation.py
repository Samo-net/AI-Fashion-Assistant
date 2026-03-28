from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.visualization import VisualizationJob


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Context used to generate this recommendation
    occasion: Mapped[Optional[str]] = mapped_column(String(80))
    weather_condition: Mapped[Optional[str]] = mapped_column(String(80))
    weather_temp_celsius: Mapped[Optional[float]] = mapped_column(Float)
    season: Mapped[Optional[str]] = mapped_column(String(50))  # harmattan, rainy, dry

    # GPT-4o output
    item_ids: Mapped[list] = mapped_column(JSON, default=[])  # list of WardrobeItem IDs
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    accessory_suggestion: Mapped[Optional[str]] = mapped_column(Text)
    gpt_model_used: Mapped[Optional[str]] = mapped_column(String(50))

    # User feedback
    accepted: Mapped[Optional[bool]] = mapped_column(Boolean)  # None = no feedback yet
    user_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5

    # Cache key for deduplication
    context_hash: Mapped[Optional[str]] = mapped_column(String(64))

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="recommendations")
    visualization_jobs: Mapped[list["VisualizationJob"]] = relationship(
        "VisualizationJob", back_populates="recommendation"
    )
