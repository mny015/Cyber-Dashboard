from datetime import datetime

from app.models import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(120), nullable=False)
    details = db.Column(db.Text, nullable=False, default="")
    ip_address = db.Column(db.String(45), nullable=False, default="")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref="audit_logs", lazy=True)
