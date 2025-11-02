"""
Bookings Blueprint
"""

from flask import Blueprint
from app.api.bookings.routes import bookings_bp

__all__ = ['bookings_bp']
