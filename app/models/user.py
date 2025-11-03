"""
User Model
"""

from extensions import db, bcrypt
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles enum"""
    GUEST = 'guest'
    HOST = 'host'
    ADMIN = 'admin'


class User(db.Model):
    """User model for authentication and profile"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))
    cnic = db.Column(db.String(15), unique=True, nullable=True)
    cnic_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_notes = db.Column(db.Text, nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    verified_by = db.relationship('User', remote_side=[id], backref='verified_users')
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # Role and status
    role = db.Column(db.Enum(UserRole), default=UserRole.GUEST, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    properties = db.relationship('Property', backref='host', lazy='dynamic', 
                                foreign_keys='Property.host_id')
    bookings = db.relationship('Booking', backref='guest', lazy='dynamic',
                              foreign_keys='Booking.guest_id')
    reviews_written = db.relationship('Review', backref='author', lazy='dynamic',
                                     foreign_keys='Review.user_id')
    
    def __init__(self, email, username, password, first_name, last_name, **kwargs):
        """Initialize user with hashed password"""
        self.email = email
        self.username = username
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        
        # Handle optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    @property
    def full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self, include_email=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'bio': self.bio,
            'profile_picture': self.profile_picture,
            'cnic': self.cnic,
            'role': self.role.value,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'cnic_verified': self.cnic_verified,
        }
        
        if include_email:
            data['email'] = self.email
            data['phone'] = self.phone
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'
