"""
Flask extensions initialization
Extensions are initialized here to avoid circular imports
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from datetime import timedelta
from pusher import Pusher
import os


# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
cors = CORS()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Using in-memory storage instead of Redis
)
if os.getenv('PUSHER_APP_ID'):
    pusher_client = Pusher(
        app_id=os.getenv('PUSHER_APP_ID'),
        key=os.getenv('PUSHER_KEY'),
        secret=os.getenv('PUSHER_SECRET'),
        cluster=os.getenv('PUSHER_CLUSTER'),
        ssl=True
    )
else:
    # Fallback to prevent crash during migrations if keys are missing
    pusher_client = None
    print("⚠️ Warning: Pusher credentials not found. Pusher is disabled.")