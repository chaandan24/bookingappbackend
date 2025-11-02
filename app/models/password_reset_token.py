"""
Password Reset Token Model
"""

from extensions import db
from datetime import datetime, timedelta
import secrets


class PasswordResetToken(db.Model):
    """Model for password reset tokens"""
    
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref='reset_tokens')
    
    def __init__(self, user_id, expiry_hours=1):
        """Initialize with auto-generated token"""
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
    
    def is_valid(self):
        """Check if token is valid"""
        return not self.used and datetime.utcnow() < self.expires_at
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        db.session.commit()
    
    @staticmethod
    def verify_token(token):
        """Verify and return token if valid"""
        reset_token = PasswordResetToken.query.filter_by(token=token).first()
        
        if not reset_token:
            return None
        
        if not reset_token.is_valid():
            return None
        
        return reset_token
    
    def __repr__(self):
        return f'<PasswordResetToken {self.token[:10]}...>'
