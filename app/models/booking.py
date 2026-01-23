"""
Booking Model
"""

from extensions import db
from datetime import datetime
from enum import Enum


class BookingStatus(str, Enum):
    """Booking status enum"""
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    REJECTED = 'rejected'


class Booking(db.Model):
    """Booking/Reservation model"""
    
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    

    
    # Booking Details
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    
    # Status
    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    
    # Pricing
    price_per_night = db.Column(db.Numeric(10, 2), nullable=False)
    nights = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    cleaning_fee = db.Column(db.Numeric(10, 2), default=0)
    service_fee = db.Column(db.Numeric(10, 2), default=0)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Payment Information
    payment_intent_id = db.Column(db.String(255))  # Stripe Payment Intent ID
    payment_status = db.Column(db.String(50), default='pending')
    
    # Additional Information
    special_requests = db.Column(db.Text)
    cancellation_reason = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        """Initialize booking"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def calculate_price(self):
        """Calculate total booking price"""
        self.nights = (self.check_out - self.check_in).days
        self.subtotal = float(self.price_per_night) * self.nights
        total = self.subtotal + float(self.cleaning_fee) + float(self.service_fee)
        self.total_price = total
        return total
    
    def confirm(self):
        """Confirm booking"""
        self.status = BookingStatus.CONFIRMED
        db.session.commit()
    
    def cancel(self, reason=None):
        """Cancel booking"""
        self.status = BookingStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        if reason:
            self.cancellation_reason = reason
        db.session.commit()
    
    def complete(self):
        """Mark booking as completed"""
        self.status = BookingStatus.COMPLETED
        db.session.commit()
    
    def can_cancel(self):
        """Check if booking can be cancelled"""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]
    
    def to_dict(self, include_property=False, include_guest=False):
        """Convert booking to dictionary"""
        data = {
            'id': self.id,
            'property_id': self.property_id,
            'guest_id': self.guest_id,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'guests': self.guests,
            'status': self.status.value,
            'price_per_night': float(self.price_per_night),
            'nights': self.nights,
            'subtotal': float(self.subtotal),
            'cleaning_fee': float(self.cleaning_fee),
            'service_fee': float(self.service_fee),
            'total_price': float(self.total_price),
            'payment_status': self.payment_status,
            'special_requests': self.special_requests,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_property:
            data['property'] = self.property.to_dict()
        
        if include_guest:
            data['guest'] = self.guest.to_dict()
        
        return data
    
    def __repr__(self):
        return f'<Booking {self.id} - Property {self.property_id}>'
