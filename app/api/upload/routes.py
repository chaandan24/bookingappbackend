"""
Image Upload Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from app.models.property import Property
from app.models.user import User
from app.services.s3_service import S3Service, LocalStorageService

upload_bp = Blueprint('upload', __name__)


def upload_property_images_internal(request, jwt_identity):
    """Upload property images"""
    try:
        current_user_id = int(jwt_identity)
        
        # Check if files were uploaded
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        
        files = request.files.getlist('images')
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No images provided'}), 400
        
        # Limit number of images
        max_images = 10
        if len(files) > max_images:
            return jsonify({'error': f'Maximum {max_images} images allowed'}), 400
        
        # Check if S3 is configured
        use_s3 = current_app.config.get('AWS_ACCESS_KEY_ID') and \
                 current_app.config.get('S3_BUCKET_NAME')
        
        # Upload images
        if use_s3:
            uploaded_urls = S3Service.upload_multiple_files(files, folder='properties', compress=True)
        else:
            # Fallback to local storage
            uploaded_urls = LocalStorageService.upload_multiple_files(files, folder='uploads/properties')
        
        if not uploaded_urls:
            return jsonify({'error': 'Failed to upload images'}), 500
        
        return uploaded_urls
        
    except Exception as e:
        current_app.logger.error(f'Image upload error: {str(e)}')
        return jsonify({'error': str(e)}), 500



@upload_bp.route('/verification_photo', methods=['POST'])
@jwt_required()
def upload_verification_photo():
    """Upload user profile picture"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        if not file:
            return jsonify({'error': 'No image provided'}), 400
        
        use_s3 = current_app.config.get('AWS_ACCESS_KEY_ID') and \
                 current_app.config.get('S3_BUCKET_NAME')
        
        # Upload image
        if use_s3:
            # Delete old profile picture if exists
            if user.verification_photo_url:
                S3Service.delete_file(user.verification_photo_url)
            
            image_url = S3Service.upload_file(file, folder='verification_photo', compress=True)
        else:
            # Fallback to local storage
            image_url = LocalStorageService.upload_file(file, folder='uploads/verification_photo')
        
        if not image_url:
            return jsonify({'error': 'Failed to upload image'}), 500
        
        # Update user profile picture
        user.verification_photo_url = image_url
        db.session.commit()
        
        return jsonify({
            'message': 'Verification photo uploaded successfully',
            'verification_photo': image_url,
            'user': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Profile picture upload error: {str(e)}')
        return jsonify({'error': str(e)}), 500

