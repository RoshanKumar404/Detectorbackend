from app import db
from datetime import datetime

class Resolution(db.Model):
    __tablename__ = 'resolutions'

    resolution_id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issues.issue_id'), unique=True, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.admin_id'), nullable=False)
    resolved_image_url = db.Column(db.String(255))
    remarks = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime, default=datetime.utcnow)
