"""
Users Blueprint
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from extensions import db
from app.services.s3_service import S3Service

users_bp = Blueprint('users', __name__)


@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile (text fields only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed text fields only
        allowed_fields = ['first_name', 'last_name', 'phone', 'bio']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field] if data[field] else None)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@users_bp.route('/me/profile-picture', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    """Upload profile picture via multipart form"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Delete old profile picture from S3
        if user.profile_picture:
            S3Service.delete_file(user.profile_picture)
        
        # Upload new picture
        new_url = S3Service.upload_file(file, folder='profile-pictures', compress=True)
        
        if not new_url:
            return jsonify({'error': 'Failed to upload image'}), 400
        
        user.profile_picture = new_url
        db.session.commit()
        
        return jsonify({
            'message': 'Profile picture updated',
            'profile_picture': new_url,
            'user': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@users_bp.route('/me/profile-picture', methods=['DELETE'])
@jwt_required()
def delete_profile_picture():
    """Delete profile picture"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.profile_picture:
            S3Service.delete_file(user.profile_picture)
            user.profile_picture = None
            db.session.commit()
        
        return jsonify({
            'message': 'Profile picture removed',
            'user': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@users_bp.route('/me/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new password are required'}), 400
        
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500