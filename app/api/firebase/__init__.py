"""
Notifications Blueprint
"""

from flask import Blueprint
from app.api.firebase.routes import firebase_bp

__all__ = ['firebase_bp']
