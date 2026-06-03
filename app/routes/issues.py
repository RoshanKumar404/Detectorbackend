from flask import Blueprint, request, jsonify
from app.models.issue import Issue
from app import db
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.services.cloudinary_service import CloudinaryService
from datetime import datetime, timedelta, timezone
from math import atan2, cos, radians, sin, sqrt
from PIL import Image, ExifTags
from io import BytesIO
import json
import os
import urllib.parse
import urllib.request
import urllib.error

issues_bp = Blueprint('issues', __name__)
cloudinary_service = CloudinaryService()

MIN_WATERLOGGED_CONFIDENCE = 0.88
NEARBY_REPORT_METERS = 100
CLUSTER_VALIDATION_METERS = 50
MIN_CLUSTER_REPORTS = 7
MIN_CLUSTER_SCORE = 7.0
RATE_LIMIT_WINDOW = timedelta(hours=1)
MAX_REPORTS_PER_WINDOW = 3
NEW_ACCOUNT_WINDOW = timedelta(days=7)
TRUSTED_ACCOUNT_WINDOW = timedelta(days=30)
MAX_PHOTO_AGE = timedelta(minutes=30)
OSM_ROAD_CHECK_RADIUS_METERS = int(os.getenv("OSM_ROAD_CHECK_RADIUS_METERS", "25"))
OSM_ROAD_CHECK_ENABLED = os.getenv("OSM_ROAD_CHECK_ENABLED", "true").lower() != "false"
OSM_ROAD_CHECK_FAIL_CLOSED = os.getenv("OSM_ROAD_CHECK_FAIL_CLOSED", "true").lower() != "false"
OSM_OVERPASS_URL = os.getenv("OSM_OVERPASS_URL", "https://overpass-api.de/api/interpreter")
ROAD_HIGHWAY_EXCLUSIONS = {
    "bridleway",
    "cycleway",
    "footway",
    "path",
    "pedestrian",
    "steps",
    "track",
}

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
        "verification_status": issue.verification_status,
        "verification_weight": issue.verification_weight,
        "verification_score": calculate_issue_score(issue),
        "fraud_flags": json.loads(issue.fraud_flags) if issue.fraud_flags else [],
        "created_at": issue.created_at.isoformat()
    }

def parse_float(value, field_name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number")

def is_valid_coordinate(latitude, longitude):
    return (
        -90 <= latitude <= 90
        and -180 <= longitude <= 180
        and not (latitude == 0 and longitude == 0)
    )

def haversine_meters(lat1, lon1, lat2, lon2):
    radius = 6371000
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    return radius * 2 * atan2(sqrt(a), sqrt(1 - a))

def gps_to_decimal(values, ref):
    degrees = float(values[0])
    minutes = float(values[1])
    seconds = float(values[2])
    decimal = degrees + minutes / 60 + seconds / 3600
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal

def extract_image_metadata(image_bytes):
    metadata = {
        "captured_at": None,
        "latitude": None,
        "longitude": None
    }
    try:
        image = Image.open(BytesIO(image_bytes))
        exif = image.getexif()
        if not exif:
            return metadata

        tag_map = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        captured = tag_map.get("DateTimeOriginal") or tag_map.get("DateTime")
        if captured:
            try:
                metadata["captured_at"] = datetime.strptime(captured, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                pass

        gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo) if hasattr(ExifTags, "IFD") else {}
        gps_map = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
        if gps_map.get("GPSLatitude") and gps_map.get("GPSLatitudeRef") and gps_map.get("GPSLongitude") and gps_map.get("GPSLongitudeRef"):
            metadata["latitude"] = gps_to_decimal(gps_map["GPSLatitude"], gps_map["GPSLatitudeRef"])
            metadata["longitude"] = gps_to_decimal(gps_map["GPSLongitude"], gps_map["GPSLongitudeRef"])
    except Exception:
        pass
    return metadata

def parse_client_timestamp(value):
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        return None

def reject(message, status_code=422, **extra):
    payload = {"error": message}
    payload.update(extra)
    return jsonify(payload), status_code

def validate_photo_timestamp(image_metadata, client_captured_at=None):
    captured_at = client_captured_at or image_metadata["captured_at"]
    if not captured_at:
        return False, "missing_capture_timestamp"

    now = datetime.utcnow() if client_captured_at else datetime.now()
    photo_age = now - captured_at
    if photo_age < timedelta(minutes=-5):
        return False, "capture_timestamp_in_future"
    if photo_age > MAX_PHOTO_AGE:
        return False, "photo_older_than_30_minutes"
    return True, None

def is_road_location(latitude, longitude):
    if not OSM_ROAD_CHECK_ENABLED:
        return True, "disabled"

    query = f"""
    [out:json][timeout:8];
    way(around:{OSM_ROAD_CHECK_RADIUS_METERS},{latitude},{longitude})["highway"];
    out tags 10;
    """
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request_obj = urllib.request.Request(
        OSM_OVERPASS_URL,
        data=data,
        headers={
            "User-Agent": "DetectorBackend/1.0",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request_obj, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
        return (False, f"osm_check_failed:{error}") if OSM_ROAD_CHECK_FAIL_CLOSED else (True, "osm_unavailable_allowed")

    for element in payload.get("elements", []):
        highway = element.get("tags", {}).get("highway")
        if highway and highway not in ROAD_HIGHWAY_EXCLUSIONS:
            return True, highway

    return False, "not_near_road"

def find_recent_nearby_report(query, latitude, longitude):
    since = datetime.utcnow() - RATE_LIMIT_WINDOW
    recent_issues = query.filter(Issue.created_at >= since).all()
    for issue in recent_issues:
        distance = haversine_meters(latitude, longitude, issue.imagelatitude, issue.imagelongitude)
        if distance <= NEARBY_REPORT_METERS:
            return issue
    return None

def count_recent_reports(query):
    since = datetime.utcnow() - RATE_LIMIT_WINDOW
    return query.filter(Issue.created_at >= since).count()

def find_nearby_cluster_issues(latitude, longitude, radius_meters=CLUSTER_VALIDATION_METERS):
    # Pre-filter with a bounding box in SQL (~1.5x the radius) to avoid full table scans.
    # 1 degree of latitude ≈ 111_000 m; longitude degree shrinks with cos(lat).
    lat_delta = radius_meters / 111_000.0
    lon_delta = radius_meters / (111_000.0 * cos(radians(latitude)) + 1e-9)
    bbox_issues = Issue.query.filter(
        Issue.prediction_result == "waterlogged",
        Issue.imagelatitude.between(latitude - lat_delta, latitude + lat_delta),
        Issue.imagelongitude.between(longitude - lon_delta, longitude + lon_delta),
    ).all()

    nearby_issues = []
    for issue in bbox_issues:
        if issue.verification_status == "flagged":
            continue
        distance = haversine_meters(latitude, longitude, issue.imagelatitude, issue.imagelongitude)
        if distance <= radius_meters:
            nearby_issues.append(issue)
    return nearby_issues

def calculate_issue_score(issue):
    return round((issue.verification_weight or 0) * (issue.confidence_score or 0), 4)

def apply_cluster_validation(latitude, longitude, fraud_flags):
    if fraud_flags:
        return [], 0

    cluster_issues = find_nearby_cluster_issues(latitude, longitude)
    cluster_score = round(sum(calculate_issue_score(issue) for issue in cluster_issues), 4)
    if len(cluster_issues) >= MIN_CLUSTER_REPORTS and cluster_score >= MIN_CLUSTER_SCORE:
        for issue in cluster_issues:
            issue.verification_status = "confirmed"
            issue.status = "confirmed"
    return cluster_issues, cluster_score

def account_weight(user):
    if not user or not user.created_at:
        return 0.5
    account_age = datetime.utcnow() - user.created_at
    if account_age < NEW_ACCOUNT_WINDOW:
        return 0.5
    if account_age >= TRUSTED_ACCOUNT_WINDOW:
        return 1.5
    return 1.0

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
                "verification_status": i.verification_status,
                "verification_weight": i.verification_weight,
                "verification_score": calculate_issue_score(i),
                "prediction": i.prediction_result,
                "image_url": i.image_url,
                "created_at": i.created_at.isoformat()
            }
        })
        
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    }), 200
@issues_bp.route('/global', methods=['GET'])
@jwt_required()
def get_global_issues():
    status = request.args.get('status')
    municipality_id = request.args.get('municipality_id')
    
    query = Issue.query
    
    if municipality_id:
        try:
            query = query.filter_by(municipality_id=int(municipality_id))
        except ValueError:
            return jsonify({"error": "Invalid municipality_id"}), 400
            
    if status:
        query = query.filter_by(status=status)
        
    issues = query.order_by(Issue.created_at.desc()).all()
    
    result = []
    for i in issues:
        user_name = i.user.name if i.user else None
        result.append({
            "id": i.issue_id,
            "user_id": i.user_id,
            "user_name": user_name,
            "municipality_id": i.municipality_id,
            "municipality_name": i.municipality_name,
            "image_url": i.image_url,
            "latitude": i.imagelatitude,
            "longitude": i.imagelongitude,
            "prediction": i.prediction_result,
            "confidence": i.confidence_score,
            "status": i.status,
            "verification_status": i.verification_status,
            "verification_weight": i.verification_weight,
            "verification_score": calculate_issue_score(i),
            "fraud_flags": json.loads(i.fraud_flags) if i.fraud_flags else [],
            "created_at": i.created_at.isoformat()
        })
        
    return jsonify(result), 200

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
    client_captured_at = parse_client_timestamp(request.form.get('captured_at'))
    device_fingerprint = request.form.get('device_fingerprint') or request.headers.get('X-Device-Fingerprint')
    location_source = request.form.get('location_source', 'gps')
    
    if not lat or not lng:
        return jsonify({"error": "Latitude and longitude are required"}), 400

    try:
        latitude = parse_float(lat, "latitude")
        longitude = parse_float(lng, "longitude")
        confidence_score = parse_float(confidence, "confidence")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if not is_valid_coordinate(latitude, longitude):
        return jsonify({"error": "Invalid report coordinates"}), 400

    normalized_prediction = prediction.strip().lower()
    if normalized_prediction != "waterlogged" or confidence_score < MIN_WATERLOGGED_CONFIDENCE:
        return jsonify({
            "error": "Report rejected: only waterlogged predictions above 88% confidence are accepted",
            "prediction": normalized_prediction,
            "confidence": confidence_score,
            "required_confidence": MIN_WATERLOGGED_CONFIDENCE
        }), 422

    image_bytes = image_file.read()
    image_file.stream.seek(0)
    image_metadata = extract_image_metadata(image_bytes)
    fraud_flags = []

    timestamp_valid, timestamp_error = validate_photo_timestamp(image_metadata, client_captured_at)
    if not timestamp_valid:
        return reject(
            "Report rejected: image capture time must be available and within the last 30 minutes",
            reason=timestamp_error,
            max_photo_age_minutes=int(MAX_PHOTO_AGE.total_seconds() // 60)
        )

    road_valid, road_reason = is_road_location(latitude, longitude)
    if not road_valid:
        return reject(
            "Report rejected: location does not appear to be on or near a mapped road",
            reason=road_reason,
            road_check_radius_meters=OSM_ROAD_CHECK_RADIUS_METERS
        )

    # Retrieve user and their designated municipality before upload.
    user_id = get_jwt_identity()
    from app.models.user import User
    user = User.query.get(int(user_id))

    recent_user_count = count_recent_reports(Issue.query.filter_by(user_id=int(user_id)))
    if recent_user_count >= MAX_REPORTS_PER_WINDOW:
        return jsonify({
            "error": "Rate limit: maximum 3 reports per user per hour",
            "limit": MAX_REPORTS_PER_WINDOW,
            "window_minutes": int(RATE_LIMIT_WINDOW.total_seconds() // 60)
        }), 429

    duplicate_for_user = find_recent_nearby_report(
        Issue.query.filter_by(user_id=int(user_id)),
        latitude,
        longitude
    )
    if duplicate_for_user:
        return jsonify({
            "error": "Rate limit: one report per user per nearby location per hour",
            "existing_issue_id": duplicate_for_user.issue_id
        }), 429

    if device_fingerprint:
        recent_device_count = count_recent_reports(Issue.query.filter_by(device_fingerprint=device_fingerprint))
        if recent_device_count >= MAX_REPORTS_PER_WINDOW:
            return jsonify({
                "error": "Rate limit: maximum 3 reports per device per hour",
                "limit": MAX_REPORTS_PER_WINDOW,
                "window_minutes": int(RATE_LIMIT_WINDOW.total_seconds() // 60)
            }), 429

        duplicate_for_device = find_recent_nearby_report(
            Issue.query.filter_by(device_fingerprint=device_fingerprint),
            latitude,
            longitude
        )
        if duplicate_for_device:
            return jsonify({
                "error": "Rate limit: this device already submitted a nearby report recently",
                "existing_issue_id": duplicate_for_device.issue_id
            }), 429

    if image_metadata["latitude"] is not None and image_metadata["longitude"] is not None:
        exif_distance = haversine_meters(
            latitude,
            longitude,
            image_metadata["latitude"],
            image_metadata["longitude"]
        )
        if exif_distance > 100:
            fraud_flags.append("exif_gps_mismatch_over_100m")
    else:
        fraud_flags.append("missing_exif_gps")

    # Upload only after hard validation passes.
    image_url = cloudinary_service.upload_image(image_file)
    if not image_url:
        return jsonify({"error": "Failed to upload image to storage"}), 500
    
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
        imagelatitude=latitude,
        imagelongitude=longitude,
        prediction_result=normalized_prediction,
        confidence_score=confidence_score,
        verification_status="flagged" if fraud_flags else "pending",
        verification_weight=account_weight(user),
        fraud_flags=json.dumps(fraud_flags),
        device_fingerprint=device_fingerprint,
        location_source=location_source,
        exif_captured_at=image_metadata["captured_at"],
        exif_latitude=image_metadata["latitude"],
        exif_longitude=image_metadata["longitude"]
    )
    db.session.add(new_issue)
    db.session.flush()
    cluster_issues, cluster_score = apply_cluster_validation(latitude, longitude, fraud_flags)
    cluster_count = len(cluster_issues)
    
    # 4. Save to Reports table as well for secondary reporting tracking
    from app.models.reports import Report
    new_report = Report(
        user_id=int(user_id),
        municipality_id=municipality_id if municipality_id else 1,  # Default fallback if not set
        municipality_name=municipality_name if municipality_name else "Ranchi Municipal Corporation (RMC)",
        issue_description=f"Automated classification: {normalized_prediction}",
        latitude=latitude,
        longitude=longitude,
        image_url=image_url
    )
    db.session.add(new_report)
    
    db.session.commit()
    
    return jsonify({
        "message": "Issue and Report created successfully",
        "issue_id": new_issue.issue_id,
        "municipality_name": new_issue.municipality_name,
        "image_url": image_url,
        "verification_status": new_issue.verification_status,
        "verification_weight": new_issue.verification_weight,
        "verification_score": calculate_issue_score(new_issue),
        "cluster_count": cluster_count,
        "cluster_score": cluster_score,
        "required_cluster_reports": MIN_CLUSTER_REPORTS,
        "required_cluster_score": MIN_CLUSTER_SCORE,
        "cluster_radius_meters": CLUSTER_VALIDATION_METERS,
        "road_check": road_reason,
        "fraud_flags": fraud_flags
    }), 201
