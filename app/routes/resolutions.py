from flask import Blueprint, request, jsonify
from app.models.issue import Issue
from app.models.resolution import Resolution
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

resolutions_bp = Blueprint('resolutions', __name__)

@resolutions_bp.route('/', methods=['POST'])
@jwt_required()
def create_resolution():
    # Admin check
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Administration access required"}), 403

    data = request.get_json()
    issue_id = data.get('issue_id')
    remarks = data.get('remarks')
    
    issue = Issue.query.get(issue_id)
    if not issue:
        return jsonify({"error": "Issue not found"}), 404
    
    admin_id = get_jwt_identity()
    municipality_id = claims.get("municipality_id")
    try:
        municipality_id = int(municipality_id)
    except (TypeError, ValueError):
        municipality_id = None

    if not municipality_id or issue.municipality_id != municipality_id:
        return jsonify({"error": "Issue does not belong to your municipality"}), 403
    
    # Create resolution record
    resolution = Resolution(
        issue_id=issue_id,
        admin_id=admin_id,
        remarks=remarks,
        resolved_image_url=data.get('resolved_image_url') # Optional
    )
    
    # Update issue status
    issue.status = 'resolved'
    
    db.session.add(resolution)
    db.session.commit()
    
    return jsonify({"message": "Issue resolved successfully"}), 201
