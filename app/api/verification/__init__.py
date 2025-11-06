from flask import Blueprint
from app.api.verification.routes import verification_bp
from app.api.verification.upload_routes import cnic_upload_bp

__all__ = ['verification_bp', 'cnic_upload_bp']