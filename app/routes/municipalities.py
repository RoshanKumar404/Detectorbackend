from flask import Blueprint, jsonify
from app.models.municiple import Municipality, Ward

municipalities_bp = Blueprint('municipalities', __name__)

@municipalities_bp.route('/', methods=['GET'])
def get_municipalities():
    municipalities = Municipality.query.order_by(Municipality.municipality_name.asc()).all()
    result = []
    for m in municipalities:
        result.append({
            "municipality_id": m.municipality_id,
            "municipality_name": m.municipality_name,
            "municipality_address": m.municipality_address,
            "municipality_contact": m.municipality_contact,
            "municipality_email": m.municipality_email
        })
    return jsonify(result), 200

@municipalities_bp.route('/<int:m_id>/wards', methods=['GET'])
def get_wards(m_id):
    wards = Ward.query.filter_by(municipality_id=m_id).order_by(Ward.ward_number.asc()).all()
    result = []
    for w in wards:
        result.append({
            "ward_id": w.ward_id,
            "ward_number": w.ward_number,
            "municipality_id": w.municipality_id
        })
    return jsonify(result), 200
