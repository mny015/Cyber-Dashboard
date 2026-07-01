"""Add notes and note access requests

Revision ID: b7d3d12c8df4
Revises: 92c44e27b3f1
Create Date: 2026-06-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b7d3d12c8df4"
down_revision = "92c44e27b3f1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notes_owner_id", "notes", ["owner_id"])
    op.create_index("ix_notes_topic_id", "notes", ["topic_id"])

    op.create_table(
        "note_access_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("note_id", sa.Integer(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("requester_admin_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["note_id"], ["notes.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["requester_admin_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_note_access_owner_id", "note_access_requests", ["owner_id"])
    op.create_index("ix_note_access_admin_id", "note_access_requests", ["requester_admin_id"])
    op.create_index("ix_note_access_topic_id", "note_access_requests", ["topic_id"])
    op.create_index("ix_note_access_note_id", "note_access_requests", ["note_id"])


def downgrade():
    op.drop_table("note_access_requests")
    op.drop_table("notes")
