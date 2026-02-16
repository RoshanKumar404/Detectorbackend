from app import db
from datetime import datetime

class Issue(db.Model):
    __tablename__ = 'issues'

    issue_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    imagelatitude = db.Column(db.Float, nullable=False)
    imagelongitude = db.Column(db.Float, nullable=False)
    prediction_result = db.Column(db.String(50))
    confidence_score = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending') # pending, verified, resolved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    resolution = db.relationship('Resolution', backref='issue', uselist=False)
