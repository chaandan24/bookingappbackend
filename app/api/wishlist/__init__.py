"""
Reviews Blueprint
"""

from flask import Blueprint
from app.api.wishlist.routes import wishlist_bp

__all__ = ['wishlist_bp']
