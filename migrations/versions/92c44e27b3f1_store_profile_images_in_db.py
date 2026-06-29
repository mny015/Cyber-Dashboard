"""Store profile images in database

Revision ID: 92c44e27b3f1
Revises: 72a91d43d1a0
Create Date: 2026-06-09 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "92c44e27b3f1"
down_revision = "72a91d43d1a0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("profile_image_data", sa.LargeBinary(length=(2 ** 32) - 1), nullable=True))
    op.add_column("users", sa.Column("profile_image_mime", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("profile_image_size", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    op.drop_column("users", "profile_image_size")
    op.drop_column("users", "profile_image_mime")
    op.drop_column("users", "profile_image_data")
