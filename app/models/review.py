"""
Review Model
"""

from extensions import db
from datetime import datetime


class Review(db.Model):
    """Review/Rating model"""
    
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    
    # Review Content
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200))
    comment = db.Column(db.Text, nullable=False)
    
    # Category Ratings (optional, 1-5 scale)
    cleanliness_rating = db.Column(db.Integer)
    accuracy_rating = db.Column(db.Integer)
    location_rating = db.Column(db.Integer)
    communication_rating = db.Column(db.Integer)
    check_in_rating = db.Column(db.Integer)
    value_rating = db.Column(db.Integer)
    
    # Status
    is_visible = db.Column(db.Boolean, default=True)
    is_flagged = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Response from host
    host_response = db.Column(db.Text)
    host_response_at = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        """Initialize review"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def add_host_response(self, response):
        """Add host response to review"""
        self.host_response = response
        self.host_response_at = datetime.utcnow()
        db.session.commit()
    
    def flag(self):
        """Flag review for moderation"""
        self.is_flagged = True
        db.session.commit()
    
    def hide(self):
        """Hide review from public view"""
        self.is_visible = False
        db.session.commit()
    
    def to_dict(self, include_user=False, include_property=False):
        """Convert review to dictionary"""
        data = {
            'id': self.id,
            'property_id': self.property_id,
            'user_id': self.user_id,
            'booking_id': self.booking_id,
            'rating': self.rating,
            'title': self.title,
            'comment': self.comment,
            'cleanliness_rating': self.cleanliness_rating,
            'accuracy_rating': self.accuracy_rating,
            'location_rating': self.location_rating,
            'communication_rating': self.communication_rating,
            'check_in_rating': self.check_in_rating,
            'value_rating': self.value_rating,
            'host_response': self.host_response,
            'host_response_at': self.host_response_at.isoformat() if self.host_response_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_user:
            data['author'] = self.author.to_dict()
        
        if include_property:
            data['property'] = self.property.to_dict()
        
        return data
    
    def __repr__(self):
        return f'<Review {self.id} - Property {self.property_id}>'
