"""
Admin Routes
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.property import Property
from app.models.booking import Booking
from extensions import db
from app.utils.decorators.admin_required import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required()
def admin_dashboard():
    """Get admin dashboard statistics"""
    try:
        # Get statistics
        total_users = User.query.count()
        total_properties = Property.query.count()
        total_bookings = Booking.query.count()
        
        pending_bookings = Booking.query.filter_by(status='pending').count()
        active_hosts = User.query.filter_by(role='host', is_active=True).count()
        active_guests = User.query.filter_by(role='guest', is_active=True).count()
        
        # Recent users
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        # Recent bookings
        recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
        
        return jsonify({
            'statistics': {
                'total_users': total_users,
                'total_properties': total_properties,
                'total_bookings': total_bookings,
                'pending_bookings': pending_bookings,
                'active_hosts': active_hosts,
                'active_guests': active_guests
            },
            'recent_users': [user.to_dict() for user in recent_users],
            'recent_bookings': [booking.to_dict() for booking in recent_bookings]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_users():
    """Get all users (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        users = User.query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict(include_email=True) for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/make-admin', methods=['POST'])
@jwt_required()
@admin_required()
def make_user_admin(user_id):
    """Make a user admin"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.is_admin:
            return jsonify({'message': 'User is already an admin'}), 200
        
        user.is_admin = True
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully made {user.full_name} an admin',
            'user': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/remove-admin', methods=['POST'])
@jwt_required()
@admin_required()
def remove_user_admin(user_id):
    """Remove admin privileges from a user"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Prevent self-demotion
        if current_user_id == user_id:
            return jsonify({'error': 'Cannot remove your own admin privileges'}), 403
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.is_admin:
            return jsonify({'message': 'User is not an admin'}), 200
        
        user.is_admin = False
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully removed admin privileges from {user.full_name}',
            'user': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500