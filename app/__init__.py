"""
Flask Application Factory
"""

from flask import Flask, jsonify, render_template
from config import config
from extensions import db, migrate, jwt, bcrypt, cors, limiter, mail
import os
from flask_jwt_extended import (
    jwt_required, 
    get_jwt_identity
)
from flask import Flask, send_from_directory, jsonify
from app.models import User

def create_app(config_name=None):
    """Application factory pattern"""
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__, static_folder='../static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Firebase-AppCheck"]
        }
    })
    limiter.init_app(app)
    mail.init_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()

    return app




def register_blueprints(app):
    """Register Flask blueprints"""
    from app.api.auth import auth_bp
    from app.api.users import users_bp
    from app.api.properties import properties_bp
    from app.api.bookings import bookings_bp
    from app.api.reviews import reviews_bp
    from app.api.payments import payments_bp
    from app.api.upload import upload_bp
    from app.api.admin.routes import admin_bp


    # API v1
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(properties_bp, url_prefix='/api/properties')
    app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
    app.register_blueprint(reviews_bp, url_prefix='/api/reviews')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'API is running'}), 200
    
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Welcome to Airbnb Clone API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'users': '/api/users',
                'properties': '/api/properties',
                'bookings': '/api/bookings',
                'reviews': '/api/reviews',
                'payments': '/api/payments'
            }
        }), 200
    @app.route('/admin/login')
    def admin_login_page():
        """Render admin login page"""
        return render_template('login.html')

    @app.route('/admin/dashboard')
    def admin_dashboard_page():
        """Render admin dashboard page"""
        return render_template('dashboard.html')

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request', 'message': str(error)}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'message': 'Insufficient permissions'}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f'Unhandled exception: {str(error)}')
        return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500