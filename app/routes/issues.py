from flask import Blueprint, request, jsonify
from app.models.issue import Issue
from app import db
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.services.cloudinary_service import CloudinaryService

issues_bp = Blueprint('issues', __name__)
cloudinary_service = CloudinaryService()

def serialize_issue(issue):
    return {
        "id": issue.issue_id,
        "user_id": issue.user_id,
        "municipality_id": issue.municipality_id,
        "municipality_name": issue.municipality_name,
        "image_url": issue.image_url,
        "latitude": issue.imagelatitude,
        "longitude": issue.imagelongitude,
        "prediction": issue.prediction_result,
        "confidence": issue.confidence_score,
        "status": issue.status,
        "created_at": issue.created_at.isoformat()
    }

@issues_bp.route('/', methods=['GET'])
@jwt_required()
def get_issues():
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    requested_user_id = request.args.get('user_id')
    status = request.args.get('status')
    
    query = Issue.query
    if claims.get("role") == "admin":
        municipality_id = claims.get("municipality_id")
        if not municipality_id:
            return jsonify([]), 200
        query = query.filter_by(municipality_id=municipality_id)
        if requested_user_id:
            query = query.filter_by(user_id=requested_user_id)
    else:
        # User sees only their reported issues
        query = query.filter_by(user_id=current_user_id)

    if status:
        query = query.filter_by(status=status)
        
    issues = query.order_by(Issue.created_at.desc()).all()
    return jsonify([serialize_issue(i) for i in issues]), 200

@issues_bp.route('/map', methods=['GET'])
@jwt_required()
def get_map_issues():
    status = request.args.get('status')
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    
    query = Issue.query
    
    if claims.get("role") == "admin":
        municipality_id = claims.get("municipality_id")
        if not municipality_id:
            return jsonify({
                "type": "FeatureCollection",
                "features": []
            }), 200
        query = query.filter_by(municipality_id=municipality_id)
    else:
        query = query.filter_by(user_id=current_user_id)

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
                "municipality_id": i.municipality_id,
                "municipality_name": i.municipality_name,
                "status": i.status,
                "prediction": i.prediction_result,
                "image_url": i.image_url,
                "created_at": i.created_at.isoformat()
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

    # 2. Retrieve user and their designated municipality
    user_id = get_jwt_identity()
    from app.models.user import User
    user = User.query.get(int(user_id))
    
    municipality_id = None
    municipality_name = None
    if user:
        municipality_id = user.municipality_id
        municipality_name = user.municipality_name

    # 3. Save to Issues Database
    new_issue = Issue(
        user_id=int(user_id),
        municipality_id=municipality_id,
        municipality_name=municipality_name,
        image_url=image_url,
        imagelatitude=float(lat),
        imagelongitude=float(lng),
        prediction_result=prediction,
        confidence_score=float(confidence)
    )
    db.session.add(new_issue)
    
    # 4. Save to Reports table as well for secondary reporting tracking
    from app.models.reports import Report
    new_report = Report(
        user_id=int(user_id),
        municipality_id=municipality_id if municipality_id else 1,  # Default fallback if not set
        municipality_name=municipality_name if municipality_name else "Ranchi Municipal Corporation (RMC)",
        issue_description=f"Automated classification: {prediction}",
        latitude=float(lat),
        longitude=float(lng),
        image_url=image_url
    )
    db.session.add(new_report)
    
    db.session.commit()
    
    return jsonify({
        "message": "Issue and Report created successfully",
        "issue_id": new_issue.issue_id,
        "municipality_name": new_issue.municipality_name,
        "image_url": image_url
    }), 201
