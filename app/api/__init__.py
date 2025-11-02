"""
API Package
"""

# Import all blueprints for easy access
from app.api.auth import auth_bp
from app.api.users import users_bp
from app.api.properties import properties_bp
from app.api.bookings import bookings_bp
from app.api.reviews import reviews_bp
from app.api.payments import payments_bp

__all__ = [
    'auth_bp',
    'users_bp',
    'properties_bp',
    'bookings_bp',
    'reviews_bp',
    'payments_bp',
]
