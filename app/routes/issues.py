from flask import Blueprint, request, jsonify
from app.models.issue import Issue
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.cloudinary_service import CloudinaryService
import json

issues_bp = Blueprint('issues', __name__)
cloudinary_service = CloudinaryService()

@issues_bp.route('/', methods=['GET'])
def get_issues():
    # Filter by user if requested, otherwise return all (for admin/map)
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    
    query = Issue.query
    if user_id:
        query = query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
        
    issues = query.all()
    return jsonify([{
        "id": i.issue_id,
        "user_id": i.user_id,
        "image_url": i.image_url,
        "latitude": i.imagelatitude,
        "longitude": i.imagelongitude,
        "prediction": i.prediction_result,
        "confidence": i.confidence_score,
        "status": i.status,
        "created_at": i.created_at.isoformat()
    } for i in issues]), 200

@issues_bp.route('/map', methods=['GET'])
def get_map_issues():
    status = request.args.get('status')
    
    query = Issue.query
    if status:
        query = query.filter_by(status=status)
        
    issues = query.all()
    
    # Format as GeoJSON
    features = []
    for i in issues:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [i.imagelongitude, i.imagelatitude]
            },
            "properties": {
                "id": i.issue_id,
                "status": i.status,
                "prediction": i.prediction_result,
                "image_url": i.image_url
            }
        })
        
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    }), 200

@issues_bp.route('/', methods=['POST'])
@jwt_required()
def create_issue():
    # Expecting multipart/form-data for image and other fields as text/JSON
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    image_file = request.files['image']
    lat = request.form.get('latitude')
    lng = request.form.get('longitude')
    prediction = request.form.get('prediction', 'waterlogged')
    confidence = request.form.get('confidence', 1.0)
    
    if not lat or not lng:
        return jsonify({"error": "Latitude and longitude are required"}), 400

    # 1. Upload to Cloudinary
    image_url = cloudinary_service.upload_image(image_file)
    if not image_url:
        return jsonify({"error": "Failed to upload image to storage"}), 500

    # 2. Save to Database
    user_id = get_jwt_identity()
    new_issue = Issue(
        user_id=user_id,
        image_url=image_url,
        imagelatitude=float(lat),
        imagelongitude=float(lng),
        prediction_result=prediction,
        confidence_score=float(confidence)
    )
    
    db.session.add(new_issue)
    db.session.commit()
    return jsonify({
        "message": "Issue reported successfully",
        "issue_id": new_issue.issue_id,
        "image_url": image_url
    }), 201
