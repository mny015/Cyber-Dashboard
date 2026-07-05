"""Add scheduled tasks

Revision ID: f4d8b2a7c901
Revises: a5c9f71d22b0
Create Date: 2026-07-04 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f4d8b2a7c901"
down_revision = "a5c9f71d22b0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "scheduled_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(length=40), nullable=False, server_default="general"),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="upcoming"),
        sa.Column("scope", sa.String(length=20), nullable=False, server_default="personal"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scheduled_tasks_user_id", "scheduled_tasks", ["user_id"])
    op.create_index("ix_scheduled_tasks_created_by", "scheduled_tasks", ["created_by"])
    op.create_index("ix_scheduled_tasks_scope_status", "scheduled_tasks", ["scope", "status"])


def downgrade():
    op.drop_index("ix_scheduled_tasks_scope_status", table_name="scheduled_tasks")
    op.drop_index("ix_scheduled_tasks_created_by", table_name="scheduled_tasks")
    op.drop_index("ix_scheduled_tasks_user_id", table_name="scheduled_tasks")
    op.drop_table("scheduled_tasks")
