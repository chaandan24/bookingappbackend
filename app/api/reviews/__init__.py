"""
Reviews Blueprint
"""

from flask import Blueprint
from app.api.reviews.routes import reviews_bp

__all__ = ['reviews_bp']
