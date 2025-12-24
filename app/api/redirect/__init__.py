"""
Properties Blueprint
"""

from flask import Blueprint
from app.api.redirect.routes import redirect_bp

__all__ = ['redirect_bp']
