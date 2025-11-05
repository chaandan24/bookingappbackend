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


@upload_bp.route('/property-images', methods=['POST'])
@jwt_required()
def upload_property_images():
    """Upload property images"""
    try:
        current_user_id = int(get_jwt_identity())
        
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
        
        return jsonify({
            'message': f'Successfully uploaded {len(uploaded_urls)} images',
            'image_urls': uploaded_urls
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Image upload error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/profile-picture', methods=['POST'])
@jwt_required()
def upload_profile_pictures():
    """Upload user profile picture"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files.getlist['images']
        
        if not file:
            return jsonify({'error': 'No image provided'}), 400
        
        use_s3 = current_app.config.get('AWS_ACCESS_KEY_ID') and \
                 current_app.config.get('S3_BUCKET_NAME')
        
        # Upload image
        if use_s3:
            # Delete old profile picture if exists
            if user.profile_picture:
                S3Service.delete_file(user.profile_picture)
            
            image_url = S3Service.upload_multiple_files(file, folder='profiles', compress=True)
        else:
            # Fallback to local storage
            image_url = LocalStorageService.upload_file(file, folder='uploads/profiles')
        
        if not image_url:
            return jsonify({'error': 'Failed to upload image'}), 500
        
        # Update user profile picture
        user.profile_picture = image_url
        db.session.commit()
        
        return jsonify({
            'message': 'Profile picture uploaded successfully',
            'profile_picture': image_url,
            'user': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Profile picture upload error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/delete-image', methods=['DELETE'])
@jwt_required()
def delete_image():
    """Delete an image from S3"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        image_url = data.get('image_url')
        if not image_url:
            return jsonify({'error': 'image_url is required'}), 400
        
        # Check if S3 is configured
        use_s3 = current_app.config.get('AWS_ACCESS_KEY_ID') and \
                 current_app.config.get('S3_BUCKET_NAME')
        
        if use_s3:
            success = S3Service.delete_file(image_url)
        else:
            # For local storage, you'd implement file deletion here
            success = True
        
        if success:
            return jsonify({
                'message': 'Image deleted successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to delete image'}), 500
        
    except Exception as e:
        current_app.logger.error(f'Image deletion error: {str(e)}')
        return jsonify({'error': str(e)}), 500
