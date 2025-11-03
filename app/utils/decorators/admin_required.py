"""
Custom decorators for route protection
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request, get_jwt_identity
from app.models.user import User

def admin_required():
    """Decorator to require admin privileges"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            
            # Check if admin claim exists
            if not claims.get('is_admin', False):
                return jsonify({'error': 'Admin privileges required'}), 403
            
            # Double-check with database
            current_user_id = int(get_jwt_identity())
            user = User.query.get(current_user_id)
            
            if not user or not user.is_admin:
                return jsonify({'error': 'Admin privileges required'}), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper