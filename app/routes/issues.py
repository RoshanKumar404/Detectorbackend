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
    prediction = request.form.get('prediction', 'waterlogged') # Default from on-device AI
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
