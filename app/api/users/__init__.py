"""
Users Blueprint
"""

from flask import Blueprint
from app.api.users.routes import users_bp

__all__ = ['users_bp']
