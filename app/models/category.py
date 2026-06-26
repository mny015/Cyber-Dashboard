from datetime import datetime

from app.models import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    color = db.Column(db.String(32), nullable=False, default="#2563eb")
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    topics = db.relationship("Topic", back_populates="category", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("owner_id", "name", name="uq_category_owner_name"),
    )
