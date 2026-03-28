"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(128), primary_key=True),  # Firebase UID
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(120), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("body_type", sa.String(50), nullable=True),
        sa.Column("skin_tone", sa.String(80), nullable=True),
        sa.Column("style_preference", sa.String(80), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("gdpr_consent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("consent_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
    )

    # ── wardrobe_tags ───────────────────────────────────────────────────────
    op.create_table(
        "wardrobe_tags",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
    )

    # ── wardrobe_items ──────────────────────────────────────────────────────
    op.create_table(
        "wardrobe_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.String(128),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("subcategory", sa.String(80), nullable=True),
        sa.Column("primary_color", sa.String(50), nullable=True),
        sa.Column("pattern", sa.String(80), nullable=True),
        sa.Column("formality", sa.String(50), nullable=True),
        sa.Column("image_url", sa.Text, nullable=True),
        sa.Column("image_s3_key", sa.Text, nullable=True),
        sa.Column("clip_embedding", sa.Text, nullable=True),  # JSON-encoded float list
        sa.Column("attributes", JSONB, nullable=True, server_default="{}"),
        sa.Column("purchase_cost", sa.Float, nullable=True),
        sa.Column("clip_processed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_index("ix_wardrobe_items_user_id", "wardrobe_items", ["user_id"])
    op.create_index("ix_wardrobe_items_category", "wardrobe_items", ["category"])

    # ── item_tag_associations ───────────────────────────────────────────────
    op.create_table(
        "item_tag_associations",
        sa.Column(
            "item_id",
            sa.Integer,
            sa.ForeignKey("wardrobe_items.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            sa.Integer,
            sa.ForeignKey("wardrobe_tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # ── recommendations ─────────────────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.String(128),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("occasion", sa.String(80), nullable=True),
        sa.Column("weather_condition", sa.String(80), nullable=True),
        sa.Column("weather_temp_celsius", sa.Float, nullable=True),
        sa.Column("season", sa.String(50), nullable=True),
        sa.Column("item_ids", JSONB, nullable=False, server_default="[]"),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("accessory_suggestion", sa.Text, nullable=True),
        sa.Column("gpt_model_used", sa.String(50), nullable=True),
        sa.Column("accepted", sa.Boolean, nullable=True),
        sa.Column("user_rating", sa.Integer, nullable=True),
        sa.Column("context_hash", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"])
    op.create_index("ix_recommendations_context_hash", "recommendations", ["context_hash"])

    # ── visualization_jobs ──────────────────────────────────────────────────
    op.create_table(
        "visualization_jobs",
        sa.Column("id", sa.String(36), primary_key=True),  # UUID
        sa.Column(
            "recommendation_id",
            sa.Integer,
            sa.ForeignKey("recommendations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("input_payload", JSONB, nullable=True),
        sa.Column("image_url", sa.Text, nullable=True),
        sa.Column("image_s3_key", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("positive_prompt", sa.Text, nullable=True),
        sa.Column("negative_prompt", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_visualization_jobs_user_id", "visualization_jobs", ["user_id"])
    op.create_index("ix_visualization_jobs_status", "visualization_jobs", ["status"])

    # ── usage_logs ──────────────────────────────────────────────────────────
    op.create_table(
        "usage_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "item_id",
            sa.Integer,
            sa.ForeignKey("wardrobe_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("occasion", sa.String(80), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "worn_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_usage_logs_item_id", "usage_logs", ["item_id"])
    op.create_index("ix_usage_logs_user_id", "usage_logs", ["user_id"])


def downgrade() -> None:
    op.drop_table("usage_logs")
    op.drop_table("visualization_jobs")
    op.drop_table("recommendations")
    op.drop_table("item_tag_associations")
    op.drop_table("wardrobe_items")
    op.drop_table("wardrobe_tags")
    op.drop_table("users")
