from flask import Blueprint, request, jsonify
from app.models.user import User
from app.models.admin import Admin
from app import db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

def resolve_municipality(municipality_id):
    if municipality_id in (None, ''):
        return None, None

    from app.models.municiple import Municipality
    try:
        municipality_id = int(municipality_id)
    except (TypeError, ValueError):
        return None, None

    municipality = Municipality.query.get(municipality_id)
    if not municipality:
        return municipality_id, None

    return municipality_id, municipality.municipality_name

# --- User Auth ---

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({"error": "Missing required fields"}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400
    
    municipality_id = data.get('municipality_id')
    ward_id = data.get('ward_id')
    municipality_id, municipality_name = resolve_municipality(municipality_id)
    if data.get('municipality_id') and not municipality_name:
        return jsonify({"error": "Invalid municipality_id"}), 400
    
    new_user = User(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone'),
        municipality_id=municipality_id,
        municipality_name=municipality_name,
        ward_id=ward_id
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing email or password"}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        access_token = create_access_token(
            identity=str(user.user_id), 
            additional_claims={"role": "user"},
            expires_delta=timedelta(days=7)
        )
        return jsonify({
            "access_token": access_token,
            "user": {
                "id": user.user_id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "municipality_id": user.municipality_id,
                "municipality_name": user.municipality_name,
                "ward_id": user.ward_id
            }
        }), 200
        
    return jsonify({"error": "Invalid email or password"}), 401

# --- Admin Auth ---

@auth_bp.route('/admin/register', methods=['POST'])
def admin_register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name') or not data.get('municipality_id'):
        return jsonify({"error": "Missing required fields"}), 400
    
    if Admin.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Admin email already registered"}), 400
    
    municipality_id, municipality_name = resolve_municipality(data.get('municipality_id'))
    if not municipality_name:
        return jsonify({"error": "Invalid municipality_id"}), 400
            
    new_admin = Admin(
        name=data['name'],
        email=data['email'],
        contact_number=data.get('contact_number'),
        municipality_id=municipality_id,
        municipality_name=municipality_name
    )
    new_admin.set_password(data['password'])
    
    db.session.add(new_admin)
    db.session.commit()
    
    return jsonify({"message": "Admin registered successfully"}), 201

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('municipality_id'):
        return jsonify({"error": "Missing email, password, or municipality_id"}), 400
    
    admin = Admin.query.filter_by(email=data['email']).first()
    try:
        requested_municipality_id = int(data.get('municipality_id'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid municipality_id"}), 400
    
    if admin and admin.check_password(data['password']) and admin.municipality_id == requested_municipality_id:
        access_token = create_access_token(
            identity=str(admin.admin_id), 
            additional_claims={
                "role": "admin",
                "municipality_id": admin.municipality_id,
                "municipality_name": admin.municipality_name
            },
            expires_delta=timedelta(days=1)
        )
        return jsonify({
            "access_token": access_token,
            "admin": {
                "id": admin.admin_id,
                "name": admin.name,
                "email": admin.email,
                "contact_number": admin.contact_number,
                "municipality_id": admin.municipality_id,
                "municipality_name": admin.municipality_name
            }
        }), 200
        
    return jsonify({"error": "Invalid email, password, or municipality"}), 401

# --- Admin User Listing API ---

@auth_bp.route('/admin/users', methods=['GET'])
@jwt_required()
def get_users():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Administration access required"}), 403

    municipality_id = claims.get("municipality_id")
    if not municipality_id:
        return jsonify([]), 200

    users = User.query.filter_by(municipality_id=municipality_id).order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        result.append({
            "user_id": u.user_id,
            "name": u.name,
            "email": u.email,
            "phone": u.phone,
            "municipality_id": u.municipality_id,
            "municipality_name": u.municipality_name,
            "ward_id": u.ward_id,
            "created_at": u.created_at.isoformat()
        })
    return jsonify(result), 200
