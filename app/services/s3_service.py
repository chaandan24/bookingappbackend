"""
AWS S3 Image Upload Service
Handles image uploads to AWS S3
"""

import boto3
from botocore.exceptions import ClientError
from flask import current_app
from werkzeug.utils import secure_filename
import os
import uuid
from PIL import Image
import io


class S3Service:
    """Service for handling S3 uploads"""
    
    @staticmethod
    def get_s3_client():
        """Get initialized S3 client"""
        return boto3.client(
            's3',
            aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
            region_name=current_app.config.get('AWS_REGION', 'us-east-1')
        )
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', 
                                                     {'png', 'jpg', 'jpeg', 'gif', 'webp'})
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    @staticmethod
    def compress_image(image_file, max_size=(1920, 1080), quality=85):
        """
        Compress and resize image
        
        Args:
            image_file: File object or bytes
            max_size: Max dimensions (width, height)
            quality: JPEG quality (1-100)
        
        Returns:
            Compressed image as bytes
        """
        try:
            # Open image
            img = Image.open(image_file)
            
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if larger than max_size
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            return output
        except Exception as e:
            current_app.logger.error(f'Image compression error: {str(e)}')
            return None
    
    @staticmethod
    def upload_file(file, folder='images', compress=True):
        """
        Upload file to S3
        
        Args:
            file: File object from request.files
            folder: S3 folder/prefix
            compress: Whether to compress image
        
        Returns:
            S3 URL or None
        """
        if not file or not S3Service.allowed_file(file.filename):
            return None
        
        try:
            s3_client = S3Service.get_s3_client()
            bucket_name = current_app.config.get('S3_BUCKET_NAME')
            
            if not bucket_name:
                current_app.logger.error('S3_BUCKET_NAME not configured')
                return None
            
            # Generate unique filename
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{file_ext}"
            s3_key = f"{folder}/{filename}"
            
            # Compress image if enabled
            if compress and file_ext in ['jpg', 'jpeg', 'png']:
                compressed_file = S3Service.compress_image(file)
                if compressed_file:
                    file_to_upload = compressed_file
                else:
                    file.seek(0)  # Reset file pointer
                    file_to_upload = file
            else:
                file_to_upload = file
            
            # Upload to S3
            s3_client.upload_fileobj(
                file_to_upload,
                bucket_name,
                s3_key,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': f'image/{file_ext}'
                }
            )
            
            # Generate URL
            s3_url = f"https://{bucket_name}.s3.{current_app.config.get('AWS_REGION', 'us-east-1')}.amazonaws.com/{s3_key}"
            
            return s3_url
            
        except ClientError as e:
            current_app.logger.error(f'S3 upload error: {str(e)}')
            return None
        except Exception as e:
            current_app.logger.error(f'Upload error: {str(e)}')
            return None
    
    @staticmethod
    def upload_multiple_files(files, folder='images', compress=True):
        """
        Upload multiple files to S3
        
        Args:
            files: List of file objects
            folder: S3 folder/prefix
            compress: Whether to compress images
        
        Returns:
            List of S3 URLs
        """
        urls = []
        for file in files:
            url = S3Service.upload_file(file, folder, compress)
            if url:
                urls.append(url)
        return urls
    
    @staticmethod
    def delete_file(s3_url):
        """
        Delete file from S3
        
        Args:
            s3_url: Full S3 URL
        
        Returns:
            Success boolean
        """
        try:
            s3_client = S3Service.get_s3_client()
            bucket_name = current_app.config.get('S3_BUCKET_NAME')
            
            # Extract key from URL
            # Format: https://bucket-name.s3.region.amazonaws.com/folder/filename.ext
            key = s3_url.split(f"{bucket_name}.s3.")[1].split('/', 1)[1]
            
            s3_client.delete_object(Bucket=bucket_name, Key=key)
            return True
            
        except Exception as e:
            current_app.logger.error(f'S3 delete error: {str(e)}')
            return False
    
    @staticmethod
    def delete_multiple_files(s3_urls):
        """
        Delete multiple files from S3
        
        Args:
            s3_urls: List of S3 URLs
        
        Returns:
            Number of successfully deleted files
        """
        deleted_count = 0
        for url in s3_urls:
            if S3Service.delete_file(url):
                deleted_count += 1
        return deleted_count


class LocalStorageService:
    """
    Fallback service for local file storage
    Use this in development if you don't have AWS S3 configured
    """
    
    @staticmethod
    def upload_file(file, folder='uploads'):
        """
        Save file locally
        
        Args:
            file: File object from request.files
            folder: Local folder to save to
        
        Returns:
            Local file path or None
        """
        if not file or not S3Service.allowed_file(file.filename):
            return None
        
        try:
            # Create upload folder if it doesn't exist
            upload_folder = os.path.join(current_app.root_path, '..', folder)
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique filename
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{file_ext}"
            file_path = os.path.join(upload_folder, filename)
            
            # Save file
            file.save(file_path)
            
            # Return relative URL
            return f"/uploads/{filename}"
            
        except Exception as e:
            current_app.logger.error(f'Local upload error: {str(e)}')
            return None
    
    @staticmethod
    def upload_multiple_files(files, folder='uploads'):
        """Upload multiple files locally"""
        urls = []
        for file in files:
            url = LocalStorageService.upload_file(file, folder)
            if url:
                urls.append(url)
        return urls
