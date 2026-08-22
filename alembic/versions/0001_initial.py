"""Initial PhotoShare schema.

Revision ID: 0001
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    role_enum = sa.Enum("user", "moderator", "admin", name="user_role", native_enum=False)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
    )
    op.create_index("ix_tags_name", "tags", ["name"])

    op.create_table(
        "photos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(512), nullable=False),
        sa.Column("public_id", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_photos_user_id", "photos", ["user_id"])
    op.create_index("ix_photos_public_id", "photos", ["public_id"])

    op.create_table(
        "photo_tags",
        sa.Column("photo_id", sa.Integer(), sa.ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("photo_id", sa.Integer(), sa.ForeignKey("photos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_comments_photo_id", "comments", ["photo_id"])
    op.create_index("ix_comments_user_id", "comments", ["user_id"])

    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("photo_id", sa.Integer(), sa.ForeignKey("photos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("value >= 1 AND value <= 5", name="ck_ratings_value_range"),
        sa.UniqueConstraint("photo_id", "user_id", name="uq_ratings_photo_user"),
    )
    op.create_index("ix_ratings_photo_id", "ratings", ["photo_id"])
    op.create_index("ix_ratings_user_id", "ratings", ["user_id"])

    op.create_table(
        "photo_transforms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("photo_id", sa.Integer(), sa.ForeignKey("photos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transformation_type", sa.String(100), nullable=False),
        sa.Column("transformed_url", sa.String(512), nullable=False),
        sa.Column("qr_code_url", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_photo_transforms_photo_id", "photo_transforms", ["photo_id"])

    op.create_table(
        "token_blacklist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token", sa.String(1024), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_token_blacklist_token", "token_blacklist", ["token"])


def downgrade() -> None:
    op.drop_table("token_blacklist")
    op.drop_table("photo_transforms")
    op.drop_table("ratings")
    op.drop_table("comments")
    op.drop_table("photo_tags")
    op.drop_table("photos")
    op.drop_table("tags")
    op.drop_table("users")
