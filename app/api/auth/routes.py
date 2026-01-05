"""
Authentication Routes with Email & Password Reset
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token,
    jwt_required, 
    get_jwt_identity
)
from extensions import db, limiter
from app.models.user import User, UserRole
from app.models.password_reset_token import PasswordResetToken
from app.services.email_service import EmailService
from datetime import datetime
from app.models.email_verification_token import EmailVerificationToken

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'username', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already taken'}), 409
        
        if data.get('role') == 'host':
            is_host = True
        else: 
            is_host = False
        
        user = User(
            email=data['email'],
            username=data['username'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            bio=data.get('bio'),
            role=data.get('role', UserRole.GUEST),
            is_host=is_host
        )
        
        db.session.add(user)
        db.session.commit()

        verification_token = EmailVerificationToken(user_id=user.id)
        db.session.add(verification_token)
        db.session.commit()

        try:
            EmailService.send_verification_email(user, verification_token.token)
        except Exception as e:
            print(f"Failed to send verification email: {str(e)}")
        
        try:
            EmailService.send_registration_email(user)
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send welcome email: {str(e)}")
        
        # Generate tokens with string user ID
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(include_email=True),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("50 per hour")
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Update last login
        user.update_last_login()
        
        # Generate tokens with string user ID
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        print(jsonify({
            'message': 'Login successful',
            'user': user.to_dict(include_email=True),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(include_email=True),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/admin/login', methods=['POST'])
@limiter.limit("5 per hour")
def admin_login():
    """Admin login - checks if user is admin"""
    try:
        data = request.get_json()
        
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if user is admin
        if not user.is_admin:
            return jsonify({'error': 'Access denied. Admin privileges required.'}), 403
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Update last login
        user.update_last_login()
        
        # Generate tokens with admin claim
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'is_admin': True}
        )
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Admin login successful',
            'user': user.to_dict(include_email=True),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'is_admin': True
        }), 200
        
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("3 per hour")
def forgot_password():
    """Request password reset"""
    try:
        data = request.get_json()
        
        email = data.get('email')
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        # Always return success to prevent email enumeration
        if not user:
            return jsonify({
                'message': 'If an account exists with this email, a password reset link has been sent'
            }), 200
        
        # Create reset token
        reset_token = PasswordResetToken(user_id=user.id)
        db.session.add(reset_token)
        db.session.commit()
        
        # Send reset email
        try:
            EmailService.send_password_reset_email(user, reset_token.token)
        except Exception as e:
            print(f"Failed to send reset email: {str(e)}")
        
        return jsonify({
            'message': 'If an account exists with this email, a password reset link has been sent'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("5 per hour")
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        
        token = data.get('token')
        new_password = data.get('new_password')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and new password are required'}), 400
        
        # Verify token
        reset_token = PasswordResetToken.verify_token(token)
        
        if not reset_token:
            return jsonify({'error': 'Invalid or expired token'}), 400
        
        # Get user and update password
        user = User.query.get(reset_token.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.set_password(new_password)
        reset_token.mark_as_used()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Password reset successful'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@auth_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """Verify user email with token"""
    
    # Get token from query params or request body
    token = request.args.get('token') or request.json.get('token') if request.is_json else None
    
    if not token:
        return jsonify({'error': 'Verification token is required'}), 400
    
    # Verify the token
    verification_token = EmailVerificationToken.verify_token(token)
    
    if not verification_token:
        return jsonify({'error': 'Invalid or expired verification token'}), 400
    
    # Get the user
    user = User.query.get(verification_token.user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if already verified
    if user.is_email_verified:
        return jsonify({'message': 'Email already verified'}), 200
    
    try:
        # Mark user as verified
        user.is_email_verified = True
        user.email_verified_at = datetime.utcnow()
        
        # Mark token as used
        verification_token.mark_as_used()
        
        # Save to database
        db.session.commit()
        
        print(f"✅ User {user.id} verified: {user.is_email_verified}")  # Debug
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {str(e)}")  # Debug
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Email verified successfully',
        'user': {
            'id': user.id,
            'email': user.email,
            'is_email_verified': user.is_email_verified
        }
    }), 200


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    from app.services.email_service import EmailService
    
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Don't reveal if email exists
        return jsonify({'message': 'If the email exists, a verification link has been sent'}), 200
    
    if user.is_email_verified:
        return jsonify({'error': 'Email already verified'}), 400
    
    # Create new verification token
    verification_token = EmailVerificationToken(user_id=user.id)
    db.session.add(verification_token)
    db.session.commit()
    
    # Send verification email
    EmailService.send_verification_email(user, verification_token.token)
    
    return jsonify({'message': 'Verification email sent'}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate fields
        if 'current_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Check current password
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client should delete token)"""
    return jsonify({
        'message': 'Logout successful'
    }), 200
