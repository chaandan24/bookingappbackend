from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.property import Property
from extensions import db

wishlist_bp = Blueprint('wishlist', __name__)

@wishlist_bp.route('/toggle/<int:property_id>', methods=['POST'])
@jwt_required()
def toggle_wishlist(property_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    wishlist = user.wishlist or []
    
    if property_id in wishlist:
        wishlist.remove(property_id)
        added = False
    else:
        wishlist.append(property_id)
        added = True
    
    user.wishlist = wishlist
    db.session.commit()
    
    return jsonify({
        'added': added,
        'wishlist': wishlist
    }), 200

@wishlist_bp.route('/', methods=['GET'])
@jwt_required()
def get_wishlist():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    wishlist_ids = user.wishlist or []
    properties = Property.query.filter(Property.id.in_(wishlist_ids)).all()
    
    return jsonify({
        'wishlist_ids': wishlist_ids,
        'properties': [p.to_dict(include_host=True) for p in properties]
    }), 200