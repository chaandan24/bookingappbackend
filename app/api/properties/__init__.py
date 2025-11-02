"""
Properties Blueprint
"""

from flask import Blueprint
from app.api.properties.routes import properties_bp

__all__ = ['properties_bp']
