"""
Email Verification Token Model
"""

from extensions import db
from datetime import datetime, timedelta
import secrets


class EmailVerificationToken(db.Model):
    """Model for email verification tokens"""
    
    __tablename__ = 'email_verification_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('verification_tokens', lazy=True))
    
    def __init__(self, user_id, expiry_hours=24):
        """Initialize verification token"""
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(hours=expiry_hours)
        self.used = False
    
    def is_expired(self):
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        return not self.used and not self.is_expired()
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.used_at = datetime.utcnow()
    
    @staticmethod
    def verify_token(token):
        """Verify a token and return it if valid"""
        verification_token = EmailVerificationToken.query.filter_by(token=token).first()
        
        if not verification_token:
            return None
        
        if not verification_token.is_valid():
            return None
        
        return verification_token
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'used': self.used,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'is_valid': self.is_valid()
        }
    
    def __repr__(self):
        return f'<EmailVerificationToken {self.id} for User {self.user_id}>'