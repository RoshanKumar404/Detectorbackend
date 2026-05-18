from app import db

class Municipality(db.Model):
    __tablename__ = 'municipalities'

    municipality_id = db.Column(db.Integer, primary_key=True)
    municipality_name = db.Column(db.String(100), nullable=False)
    municipality_address = db.Column(db.String(255))
    municipality_contact = db.Column(db.String(20))
    municipality_email = db.Column(db.String(120))

    # Relationships
    admins = db.relationship('Admin', backref='municipality', lazy=True)
    users = db.relationship('User', backref='municipality', lazy=True)
    wards = db.relationship('Ward', backref='municipality', lazy=True, cascade="all, delete-orphan")
    reports = db.relationship('Report', backref='municipality', lazy=True)
    issues = db.relationship('Issue', backref='municipality', lazy=True)

class Ward(db.Model):
    __tablename__ = 'wards'

    ward_id = db.Column(db.Integer, primary_key=True)
    ward_number = db.Column(db.Integer, nullable=False)
    municipality_id = db.Column(db.Integer, db.ForeignKey('municipalities.municipality_id'), nullable=False)

    # Relationships
    users = db.relationship('User', backref='ward', lazy=True)
