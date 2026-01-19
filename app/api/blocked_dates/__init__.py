"""
Bookings Blueprint
"""

from flask import Blueprint
from app.api.blocked_dates.routes import blocked_dates_bp

__all__ = ['blocked_dates_bp']
