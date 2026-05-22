from app import db
from datetime import datetime

class Issue(db.Model):
    __tablename__ = 'issues'

    issue_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    municipality_id = db.Column(db.Integer, db.ForeignKey('municipalities.municipality_id'), nullable=True)
    municipality_name = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.String(255), nullable=False)
    imagelatitude = db.Column(db.Float, nullable=False)
    imagelongitude = db.Column(db.Float, nullable=False)
    prediction_result = db.Column(db.String(50))
    confidence_score = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending') # pending, verified, resolved, rejected
    verification_status = db.Column(db.String(20), default='pending') # pending, trusted, flagged
    verification_weight = db.Column(db.Float, default=1.0)
    fraud_flags = db.Column(db.Text, nullable=True)
    device_fingerprint = db.Column(db.String(255), nullable=True)
    location_source = db.Column(db.String(30), nullable=True)
    exif_captured_at = db.Column(db.DateTime, nullable=True)
    exif_latitude = db.Column(db.Float, nullable=True)
    exif_longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    resolution = db.relationship('Resolution', backref='issue', uselist=False)
