from flask import Blueprint, request, jsonify
from app.models.user import User
from app.models.admin import Admin
from app import db
from flask_jwt_extended import create_access_token
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

# --- User Auth ---

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({"error": "Missing required fields"}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400
    
    new_user = User(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone')
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
                "email": user.email
            }
        }), 200
        
    return jsonify({"error": "Invalid email or password"}), 401

# --- Admin Auth ---

@auth_bp.route('/admin/register', methods=['POST'])
def admin_register():
    # Note: In a real app, you might want to restrict this or use a master key
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({"error": "Missing required fields"}), 400
    
    if Admin.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Admin email already registered"}), 400
    
    new_admin = Admin(
        name=data['name'],
        email=data['email']
    )
    new_admin.set_password(data['password'])
    
    db.session.add(new_admin)
    db.session.commit()
    
    return jsonify({"message": "Admin registered successfully"}), 201

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing email or password"}), 400
    
    admin = Admin.query.filter_by(email=data['email']).first()
    
    if admin and admin.check_password(data['password']):
        access_token = create_access_token(
            identity=str(admin.admin_id), 
            additional_claims={"role": "admin"},
            expires_delta=timedelta(days=1)
        )
        return jsonify({
            "access_token": access_token,
            "admin": {
                "id": admin.admin_id,
                "name": admin.name,
                "email": admin.email
            }
        }), 200
        
    return jsonify({"error": "Invalid email or password"}), 401
