"""
CNIC Verification API Routes
Create this file as: app/api/verification/routes.py
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from extensions import db
from functools import wraps

verification_bp = Blueprint('verification', __name__, url_prefix='/api/verification')


def admin_required(fn):
    """Decorator to check if user is admin"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # You'll need to add an 'is_admin' field to your User model
        # Or check against specific admin user IDs
        if not user or not getattr(user, 'is_admin', False):
            return jsonify({'error': 'Admin access required'}), 403
        
        return fn(*args, **kwargs)
    return wrapper


@verification_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_cnic():
    """Submit CNIC for verification"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    cnic = data.get('cnic', '').strip()
    
    # Validate CNIC format (Pakistani CNIC: 13 digits, format: XXXXX-XXXXXXX-X)
    if not cnic:
        return jsonify({'error': 'CNIC is required'}), 400
    
    # Remove dashes for storage
    cnic_clean = cnic.replace('-', '')
    
    if len(cnic_clean) != 13 or not cnic_clean.isdigit():
        return jsonify({'error': 'Invalid CNIC format. Must be 13 digits'}), 400
    
    # Check if CNIC already exists
    existing = User.query.filter_by(cnic=cnic_clean).first()
    if existing and existing.id != user.id:
        return jsonify({'error': 'This CNIC is already registered'}), 400
    
    user.cnic = cnic_clean
    user.cnic_verified = False  # Reset verification status on new submission
    user.verification_notes = 'Pending verification'
    db.session.commit()
    
    return jsonify({
        'message': 'CNIC submitted successfully. Awaiting verification.',
        'user': user.to_dict(include_email=True, include_cnic=True)
    }), 200


@verification_bp.route('/status', methods=['GET'])
@jwt_required()
def get_verification_status():
    """Get current user's verification status"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'cnic_submitted': user.cnic is not None,
        'cnic_verified': user.cnic_verified,
        'verified_at': user.verified_at.isoformat() if user.verified_at else None,
        'verification_notes': user.verification_notes
    }), 200


@verification_bp.route('/pending', methods=['GET'])
@admin_required
def get_pending_verifications():
    """Get all users pending verification (Admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Users with CNIC but not verified
    pending_users = User.query.filter(
        User.cnic.isnot(None),
        User.cnic_verified == False
    ).order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [user.to_dict(include_email=True, include_cnic=True)  # Add include_cnic=True
                  for user in pending_users.items],
        'total': pending_users.total,
        'pages': pending_users.pages,
        'current_page': page
    }), 200


@verification_bp.route('/verify/<int:user_id>', methods=['POST'])
@admin_required
def verify_user(user_id):
    """Verify a user's CNIC (Admin only)"""
    current_admin_id = get_jwt_identity()
    admin = User.query.get(current_admin_id)
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.cnic:
        return jsonify({'error': 'User has not submitted CNIC'}), 400
    
    data = request.get_json()
    notes = data.get('notes', 'Verified by admin')
    
    user.verify_cnic(admin, notes)
    
    return jsonify({
        'message': 'User verified successfully',
        'user': user.to_dict(include_email=True, include_cnic=True)
    }), 200


@verification_bp.route('/reject/<int:user_id>', methods=['POST'])
@admin_required
def reject_user(user_id):
    """Reject a user's CNIC verification (Admin only)"""
    current_admin_id = get_jwt_identity()
    admin = User.query.get(current_admin_id)
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    notes = data.get('notes', '')
    
    if not notes:
        return jsonify({'error': 'Rejection reason is required'}), 400
    
    user.reject_verification(admin, notes)
    
    return jsonify({
        'message': 'Verification rejected',
        'user': user.to_dict(include_email=True, include_cnic=True)
    }), 200


@verification_bp.route('/verified', methods=['GET'])
@admin_required
def get_verified_users():
    """Get all verified users (Admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    verified_users = User.query.filter_by(
        cnic_verified=True
    ).order_by(User.verified_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [user.to_dict(include_email=True, include_cnic=True) 
                  for user in verified_users.items],
        'total': verified_users.total,
        'pages': verified_users.pages,
        'current_page': page
    }), 200


@verification_bp.route('/stats', methods=['GET'])
@admin_required
def get_verification_stats():
    """Get verification statistics (Admin only)"""
    total_users = User.query.count()
    verified_users = User.query.filter_by(cnic_verified=True).count()
    pending_users = User.query.filter(
        User.cnic.isnot(None),
        User.cnic_verified == False
    ).count()
    no_cnic = User.query.filter(User.cnic.is_(None)).count()
    
    return jsonify({
        'total_users': total_users,
        'verified_users': verified_users,
        'pending_verification': pending_users,
        'no_cnic_submitted': no_cnic,
        'verification_rate': round((verified_users / total_users * 100), 2) if total_users > 0 else 0
    }), 200