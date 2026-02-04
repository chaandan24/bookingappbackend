"""
Bookings Blueprint
"""

from flask import Blueprint
from app.api.complaints.routes import complaints_bp

__all__ = ['complaints_bp']
