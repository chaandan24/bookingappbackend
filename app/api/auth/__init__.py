"""
Authentication Blueprint
"""

from flask import Blueprint
from app.api.auth.routes import auth_bp

__all__ = ['auth_bp']
