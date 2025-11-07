"""
CNIC Image Upload Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from app.models.user import User
from app.services.s3_service import S3Service
from werkzeug.utils import secure_filename
import os

cnic_upload_bp = Blueprint('cnic_upload', __name__)


@cnic_upload_bp.route('/upload-cnic-image', methods=['POST'])
@jwt_required()
def upload_cnic_image():
    """Upload CNIC image for verification"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if CNIC number is submitted
        if not user.cnic:
            return jsonify({'error': 'Please submit your CNIC number first'}), 400
        
        # Check if file was uploaded
        if 'cnic_image' not in request.files:
            return jsonify({'error': 'No CNIC image provided'}), 400
        
        file = request.files['cnic_image']
        
        if not file or file.filename == '':
            return jsonify({'error': 'No CNIC image provided'}), 400
        
        allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, PDF'}), 400
        
        # Check if S3 is configured
        use_s3 = current_app.config.get('AWS_ACCESS_KEY_ID') and \
                 current_app.config.get('S3_BUCKET_NAME')
        
        if use_s3:
            if user.cnic_image_url:
                S3Service.delete_file(user.cnic_image_url)
            
            # Upload to S3
            compress = file_ext in ['png', 'jpg', 'jpeg']  # Don't compress PDFs
            image_url = S3Service.upload_file(file, folder='cnic', compress=compress)
            
            if not image_url:
                return jsonify({'error': 'Failed to upload CNIC image 1'}), 500
        else:
            # Fallback to local storage
            from app.services.s3_service import LocalStorageService
            image_url = LocalStorageService.upload_file(file, folder='uploads/cnic')
            
            if not image_url:
                return jsonify({'error': 'Failed to upload CNIC image 2'}), 500
        
        # Update user CNIC image URL
        user.cnic_image_url = image_url
        user.cnic_verified = False  # Reset verification status
        user.verification_notes = 'CNIC image uploaded, pending verification'
        
        db.session.commit()
        
        return jsonify({
            'message': 'CNIC image uploaded successfully',
            'cnic_image_url': image_url,
            'user': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'CNIC image upload error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@cnic_upload_bp.route('/my-cnic-image', methods=['GET'])
@jwt_required()
def get_my_cnic_image():
    """Get current user's CNIC image URL"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'cnic_image_url': user.cnic_image_url,
            'cnic': user.cnic,
            'cnic_verified': user.cnic_verified,
            'verification_notes': user.verification_notes
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500