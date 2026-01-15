"""
Notifications Blueprint
"""

from flask import Blueprint
from app.api.notifications.routes import notifications_bp

__all__ = ['notifications_bp']
