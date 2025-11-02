"""
Upload Blueprint
"""

from flask import Blueprint
from app.api.upload.routes import upload_bp

__all__ = ['upload_bp']
