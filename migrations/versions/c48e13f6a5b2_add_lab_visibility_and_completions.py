"""Add lab visibility and completions

Revision ID: c48e13f6a5b2
Revises: b7d3d12c8df4
Create Date: 2026-06-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c48e13f6a5b2"
down_revision = "b7d3d12c8df4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("lab_references", sa.Column("visibility", sa.String(length=20), nullable=False, server_default="personal"))
    op.add_column("lab_references", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0"))
    op.create_table(
        "lab_completions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lab_id"], ["lab_references.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lab_id", "user_id", name="uq_lab_completion_user"),
    )
    op.create_index("ix_lab_completions_user_id", "lab_completions", ["user_id"])


def downgrade():
    op.drop_table("lab_completions")
    op.drop_column("lab_references", "is_deleted")
    op.drop_column("lab_references", "visibility")
