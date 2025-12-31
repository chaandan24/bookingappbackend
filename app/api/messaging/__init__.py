"""
Payments Blueprint
"""

from flask import Blueprint
from app.api.messaging.routes import messaging_bp

__all__ = ['messaging_bp']
