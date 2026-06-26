from datetime import datetime

from app.models import db


class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.String(40), nullable=False, default="planned")
    priority = db.Column(db.String(40), nullable=False, default="medium")
    notes = db.Column(db.Text, nullable=False, default="")
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship("Category", back_populates="topics", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("owner_id", "slug", name="uq_topic_owner_slug"),
    )
