"""
Payments Blueprint
"""

from flask import Blueprint
from app.api.payments.routes import payments_bp

__all__ = ['payments_bp']
