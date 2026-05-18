from app import db
from datetime import datetime

class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    municipality_id = db.Column(db.Integer, db.ForeignKey('municipalities.municipality_id'), nullable=False)
    municipality_name = db.Column(db.String(100), nullable=False)
    issue_description = db.Column(db.Text)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, verified, resolved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)