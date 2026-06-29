"""Add user profile fields

Revision ID: 72a91d43d1a0
Revises: 38bb8f84a4f7
Create Date: 2026-06-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "72a91d43d1a0"
down_revision = "38bb8f84a4f7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("profile_bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("profile_image", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("users", "profile_image")
    op.drop_column("users", "profile_bio")
