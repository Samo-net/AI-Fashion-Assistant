from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.wardrobe import WardrobeItem
    from app.models.recommendation import Recommendation


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)  # Firebase UID
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(120))
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)

    # Profile
    body_type: Mapped[Optional[str]] = mapped_column(String(50))  # e.g. slim, athletic, plus-size
    skin_tone: Mapped[Optional[str]] = mapped_column(String(80))  # e.g. deep brown, caramel, ebony
    style_preference: Mapped[Optional[str]] = mapped_column(String(80))  # casual, traditional, formal, mix
    city: Mapped[Optional[str]] = mapped_column(String(100))  # Nigerian city for weather
    state: Mapped[Optional[str]] = mapped_column(String(100))

    # Consent & compliance
    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_timestamp: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    wardrobe_items: Mapped[list["WardrobeItem"]] = relationship(
        "WardrobeItem", back_populates="owner", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="user", cascade="all, delete-orphan"
    )
