"""
Property Model
"""

from extensions import db
from datetime import datetime
from enum import Enum


class PropertyType(str, Enum):
    """Property type enum"""
    APARTMENT = 'apartment'
    HOUSE = 'house'
    VILLA = 'villa'
    CABIN = 'cabin'
    CONDO = 'condo'
    STUDIO = 'studio'
    LOFT = 'loft'
    HOTEL_ROOM = 'hotel_room'
    HOTEL_SUITE = 'hotel_suite'
    OTHER = 'other'


class PropertyStatus(str, Enum):
    """Property status enum"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    PENDING = 'pending'
    SUSPENDED = 'suspended'


class Property(db.Model):
    """Property/Listing model"""
    
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Basic Information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    property_type = db.Column(db.Enum(PropertyType), nullable=False)
    status = db.Column(db.Enum(PropertyStatus), default=PropertyStatus.ACTIVE)
    
    # Location
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20))
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Property Details
    bedrooms = db.Column(db.Integer, nullable=False)
    bathrooms = db.Column(db.Float, nullable=False)
    max_guests = db.Column(db.Integer, nullable=False)
    square_feet = db.Column(db.Integer)
    
    # Pricing
    price_per_night = db.Column(db.Numeric(10, 2), nullable=False)
    cleaning_fee = db.Column(db.Numeric(10, 2), default=0)
    service_fee_percentage = db.Column(db.Float, default=10.0)
    
    # Amenities (stored as JSON array)
    amenities = db.Column(db.JSON, default=list)
    
    # House Rules
    check_in_time = db.Column(db.Time)
    check_out_time = db.Column(db.Time)
    min_nights = db.Column(db.Integer, default=1)
    max_nights = db.Column(db.Integer)
    cancellation_policy = db.Column(db.String(50), default='flexible')
    
    # Images
    images = db.Column(db.JSON, default=list)  # Array of image URLs
    
    # Statistics
    view_count = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='property', lazy='dynamic')
    reviews = db.relationship('Review', backref='property', lazy='dynamic')
    
    def __init__(self, **kwargs):
        """Initialize property"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def increment_views(self):
        """Increment view count"""
        self.view_count += 1
        db.session.commit()
    
    def update_rating(self):
        """Recalculate average rating from reviews"""
        reviews = self.reviews.all()
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            self.average_rating = round(total_rating / len(reviews), 2)
            self.total_reviews = len(reviews)
        else:
            self.average_rating = 0.0
            self.total_reviews = 0
        db.session.commit()
    
    def is_available(self, check_in, check_out):
        """Check if property is available for given dates"""
        from app.models.booking import Booking, BookingStatus
        
        # Check for overlapping bookings
        overlapping_bookings = Booking.query.filter(
            Booking.property_id == self.id,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
            Booking.check_in < check_out,
            Booking.check_out > check_in
        ).first()
        
        return overlapping_bookings is None
    
    def calculate_total_price(self, check_in, check_out):
        """Calculate total price for date range"""
        nights = (check_out - check_in).days
        subtotal = float(self.price_per_night) * nights
        cleaning = float(self.cleaning_fee)
        service_fee = subtotal * (self.service_fee_percentage / 100)
        total = subtotal + cleaning + service_fee
        
        return {
            'nights': nights,
            'price_per_night': float(self.price_per_night),
            'subtotal': subtotal,
            'cleaning_fee': cleaning,
            'service_fee': service_fee,
            'total': total
        }
    
    def to_dict(self, include_host=False):
        """Convert property to dictionary"""
        data = {
            'id': self.id,
            'host_id': self.host_id,
            'title': self.title,
            'description': self.description,
            'property_type': self.property_type.value,
            'status': self.status.value,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'max_guests': self.max_guests,
            'square_feet': self.square_feet,
            'price_per_night': float(self.price_per_night),
            'cleaning_fee': float(self.cleaning_fee),
            'amenities': self.amenities,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'min_nights': self.min_nights,
            'max_nights': self.max_nights,
            'cancellation_policy': self.cancellation_policy,
            'images': self.images,
            'view_count': self.view_count,
            'average_rating': self.average_rating,
            'total_reviews': self.total_reviews,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_host:
            data['host'] = self.host.to_dict()
        
        return data
    
    def __repr__(self):
        return f'<Property {self.title}>'
