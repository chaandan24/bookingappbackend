from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from app.models.blocked_date import BlockedDate
from app.models.property import Property
from datetime import datetime

blocked_dates_bp = Blueprint('blocked_dates', __name__)

@blocked_dates_bp.route('/<int:property_id>/block', methods=['POST'])
@jwt_required()
def block_date(property_id):
    """Block a date for a property"""
    try:
        current_user_id = int(get_jwt_identity())
        property = Property.query.get(property_id)
        
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        if property.host_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        date_str = data.get('date')  # YYYY-MM-DD format
        reason = data.get('reason')
        
        if not date_str:
            return jsonify({'error': 'date required'}), 400
        
        blocked_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Check if already blocked
        existing = BlockedDate.query.filter_by(
            property_id=property_id,
            blocked_date=blocked_date
        ).first()
        
        if existing:
            return jsonify({'error': 'Date already blocked'}), 400
        
        new_block = BlockedDate(
            property_id=property_id,
            blocked_date=blocked_date,
            reason=reason
        )
        
        db.session.add(new_block)
        db.session.commit()
        
        return jsonify({'message': 'Date blocked', 'data': new_block.to_dict()}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@blocked_dates_bp.route('/<int:property_id>/unblock', methods=['POST'])
@jwt_required()
def unblock_date(property_id):
    """Unblock a date for a property"""
    try:
        current_user_id = int(get_jwt_identity())
        property = Property.query.get(property_id)
        
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        if property.host_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        date_str = data.get('date')
        
        if not date_str:
            return jsonify({'error': 'date required'}), 400
        
        blocked_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        blocked = BlockedDate.query.filter_by(
            property_id=property_id,
            blocked_date=blocked_date
        ).first()
        
        if not blocked:
            return jsonify({'error': 'Date not blocked'}), 404
        
        db.session.delete(blocked)
        db.session.commit()
        
        return jsonify({'message': 'Date unblocked'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@blocked_dates_bp.route('/<int:property_id>/blocked-dates', methods=['GET'])
@jwt_required()
def get_blocked_dates(property_id):
    """Get all blocked dates for a property"""
    try:
        current_user_id = int(get_jwt_identity())
        property = Property.query.get(property_id)
        
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        if property.host_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        blocked_dates = BlockedDate.query.filter_by(property_id=property_id).all()
        
        return jsonify({
            'property_id': property_id,
            'blocked_dates': [bd.to_dict() for bd in blocked_dates]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500