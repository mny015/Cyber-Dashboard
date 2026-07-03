"""Normalize database to third normal form

Revision ID: e31a0b8c92d4
Revises: c48e13f6a5b2
Create Date: 2026-06-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e31a0b8c92d4"
down_revision = "c48e13f6a5b2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "profile_images",
        sa.Column("image_hash", sa.String(length=64), nullable=False),
        sa.Column("image_data", sa.LargeBinary(length=(2 ** 32) - 1), nullable=False),
        sa.Column("mime_type", sa.String(length=80), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("image_hash"),
    )
    op.execute(
        """
        INSERT IGNORE INTO profile_images
            (image_hash, image_data, mime_type, byte_size, created_at)
        SELECT profile_image, profile_image_data, profile_image_mime, profile_image_size, NOW()
        FROM users
        WHERE profile_image_data IS NOT NULL AND CHAR_LENGTH(profile_image) = 64
        """
    )
    op.drop_column("users", "profile_image_data")
    op.drop_column("users", "profile_image_mime")
    op.drop_column("users", "profile_image_size")
    op.alter_column(
        "users",
        "profile_image",
        existing_type=sa.String(length=255),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
    op.create_foreign_key(
        "fk_users_profile_image",
        "users",
        "profile_images",
        ["profile_image"],
        ["image_hash"],
    )

    lab_platforms = op.create_table(
        "lab_platforms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_lab_platform_name"),
        sa.UniqueConstraint("slug", name="uq_lab_platform_slug"),
    )
    op.bulk_insert(
        lab_platforms,
        [
            {"id": 1, "name": "picoCTF", "slug": "picoctf"},
            {"id": 2, "name": "TryHackMe", "slug": "tryhackme"},
            {"id": 3, "name": "Hack The Box", "slug": "hack-the-box"},
            {"id": 4, "name": "PortSwigger", "slug": "portswigger"},
            {"id": 5, "name": "Other", "slug": "other"},
        ],
    )
    op.add_column("lab_references", sa.Column("platform_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE lab_references AS labs
        JOIN lab_platforms AS platforms ON platforms.name = labs.vendor
        SET labs.platform_id = platforms.id
        """
    )
    op.execute(
        """
        UPDATE lab_references
        SET platform_id = (SELECT id FROM lab_platforms WHERE slug = 'other')
        WHERE platform_id IS NULL
        """
    )
    op.alter_column("lab_references", "platform_id", existing_type=sa.Integer(), nullable=False)
    op.create_index("ix_lab_references_platform_id", "lab_references", ["platform_id"])
    op.create_foreign_key(
        "fk_lab_references_platform",
        "lab_references",
        "lab_platforms",
        ["platform_id"],
        ["id"],
    )
    op.drop_column("lab_references", "vendor")

    op.drop_constraint("fk_note_access_owner", "note_access_requests", type_="foreignkey")
    op.drop_index("ix_note_access_owner_id", table_name="note_access_requests")
    op.drop_column("note_access_requests", "owner_id")


def downgrade():
    op.add_column("note_access_requests", sa.Column("owner_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE note_access_requests AS requests
        JOIN topics ON topics.id = requests.topic_id
        SET requests.owner_id = topics.owner_id
        """
    )
    op.alter_column("note_access_requests", "owner_id", existing_type=sa.Integer(), nullable=False)
    op.create_index("ix_note_access_owner_id", "note_access_requests", ["owner_id"])
    op.create_foreign_key(
        "fk_note_access_owner",
        "note_access_requests",
        "users",
        ["owner_id"],
        ["id"],
    )

    op.add_column("lab_references", sa.Column("vendor", sa.String(length=120), nullable=True))
    op.execute(
        """
        UPDATE lab_references AS labs
        JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
        SET labs.vendor = platforms.name
        """
    )
    op.alter_column("lab_references", "vendor", existing_type=sa.String(length=120), nullable=False)
    op.drop_constraint("fk_lab_references_platform", "lab_references", type_="foreignkey")
    op.drop_index("ix_lab_references_platform_id", table_name="lab_references")
    op.drop_column("lab_references", "platform_id")
    op.drop_table("lab_platforms")

    op.drop_constraint("fk_users_profile_image", "users", type_="foreignkey")
    op.add_column("users", sa.Column("profile_image_data", sa.LargeBinary(length=(2 ** 32) - 1), nullable=True))
    op.add_column("users", sa.Column("profile_image_mime", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("profile_image_size", sa.Integer(), nullable=False, server_default="0"))
    op.execute(
        """
        UPDATE users
        JOIN profile_images ON profile_images.image_hash = users.profile_image
        SET users.profile_image_data = profile_images.image_data,
            users.profile_image_mime = profile_images.mime_type,
            users.profile_image_size = profile_images.byte_size
        """
    )
    op.alter_column(
        "users",
        "profile_image",
        existing_type=sa.String(length=64),
        type_=sa.String(length=255),
        existing_nullable=True,
    )
    op.drop_table("profile_images")
