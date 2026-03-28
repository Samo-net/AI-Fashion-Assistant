import json
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey, Integer, Float
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import JSON
from app.core.database import Base
from typing import Optional, TYPE_CHECKING


class FlexVector(TypeDecorator):
    """
    pgvector Vector on PostgreSQL; JSON-encoded Text on SQLite (for tests).
    Stores and returns a list[float].
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim: int):
        self.dim = dim
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value  # pgvector accepts a plain list
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value  # pgvector returns a list natively
        if isinstance(value, str):
            return json.loads(value)
        return value

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.usage_log import UsageLog


class WardrobeTag(Base):
    __tablename__ = "wardrobe_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    items: Mapped[list["WardrobeItem"]] = relationship(
        "WardrobeItem", secondary="item_tag_associations", back_populates="tags"
    )


class ItemTagAssociation(Base):
    __tablename__ = "item_tag_associations"

    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("wardrobe_items.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("wardrobe_tags.id", ondelete="CASCADE"), primary_key=True
    )


class WardrobeItem(Base):
    __tablename__ = "wardrobe_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Item metadata
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Category — supports Nigerian + Western garments
    category: Mapped[str] = mapped_column(
        String(80), nullable=False
    )  # tops, bottoms, ankara, agbada, kaftan, aso-oke, lace, senator, accessories, footwear, dress, outerwear
    subcategory: Mapped[Optional[str]] = mapped_column(String(80))

    # Visual attributes (auto-filled by CLIP)
    primary_color: Mapped[Optional[str]] = mapped_column(String(50))
    pattern: Mapped[Optional[str]] = mapped_column(String(80))  # solid, ankara-print, stripe, lace, etc.
    formality: Mapped[Optional[str]] = mapped_column(String(50))  # casual, smart-casual, formal, traditional

    # Image
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    image_s3_key: Mapped[Optional[str]] = mapped_column(Text)

    # CLIP embedding (512-dim) — pgvector on PostgreSQL, JSON text on SQLite
    clip_embedding: Mapped[Optional[list]] = mapped_column(FlexVector(512))

    # Extra attributes as JSON (brand, purchase_date, cost, etc.)
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, default={})

    # Cost for cost-per-wear tracking
    purchase_cost: Mapped[Optional[float]] = mapped_column(Float)

    # CLIP processing state
    clip_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="wardrobe_items")
    tags: Mapped[list["WardrobeTag"]] = relationship(
        "WardrobeTag", secondary="item_tag_associations", back_populates="items"
    )
    usage_logs: Mapped[list["UsageLog"]] = relationship(
        "UsageLog", back_populates="item", cascade="all, delete-orphan"
    )
