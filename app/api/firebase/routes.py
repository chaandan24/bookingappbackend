from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
import firebase_admin
from firebase_admin import credentials, messaging, app_check
from app.models import User
from extensions import db
from datetime import datetime
from functools import wraps
import os

firebase_bp = Blueprint('firebase', __name__)

# Initialize Firebase (Ensure this runs only once in your app factory usually, 
# but here is fine if this is your entry point)
if not firebase_admin._apps:
    # Option 1: Use an environment variable (Best Practice)
    # In your .env file add: FIREBASE_CRED_PATH=qimbl-449f5-e1474119430e.json
    cred_path = os.getenv('FIREBASE_CRED_PATH')

    # Option 2: Dynamic fallback (If env var is missing, look in current directory)
    if not cred_path:
        base_dir = os.path.abspath(os.path.dirname(__file__)) # Gets 'app/' folder
        # Adjust '..' to go up one level if the json file is in the root
        cred_path = os.path.join(base_dir, '../../..', 'qimbl-449f5-e1474119430e.json')

    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        print(f"⚠️ Warning: Firebase credentials not found at {cred_path}")


# --- PUSH NOTIFICATION HELPER ---
def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None):
    """
    Sends a push notification to a single device.
    Returns the message ID on success, None on failure.
    """
    if not fcm_token:
        return None
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority='high', # wake up the device immediately
                notification=messaging.AndroidNotification(
                    channel_id='high_importance_channel', # <--- MUST MATCH YOUR FLUTTER ID
                    priority='high', # For older versions
                    default_sound=True,
                    default_vibrate_timings=True
                ),
            ),
        )
        return messaging.send(message)
    except messaging.UnregisteredError:
        # Token is invalid/expired - clear it from the database
        user = User.query.filter_by(fcm_token=fcm_token).first()
        if user:
            user.fcm_token = None
            db.session.commit()
        return None
    except Exception as e:
        print(f"FCM send error: {e}")
        return None


def notify_user(user_id: int, title: str, body: str, data: dict = None):
    user = User.query.get(user_id)
    
    # 1. Check if user exists
    if not user:
        print(f"❌ Notify User: User {user_id} not found.")
        return None
        
    # 2. Check if token exists
    if not user.fcm_token:
        print(f"⚠️ Notify User: User {user_id} has NO FCM TOKEN in DB.")
        return None

    print(f"🚀 Sending push to User {user_id} with token: {user.fcm_token[:10]}...")
    return send_push_notification(user.fcm_token, title, body, data)


def require_app_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        app_check_token = request.headers.get("X-Firebase-App-Check")
        if not app_check_token:
            return jsonify({"error": "Missing App Check Token", "code": "NO_APP_CHECK"}), 401

        try:
            app_check.verify_token(app_check_token)
            return f(*args, **kwargs)
        except Exception as e:
            print(f"App Check failed: {e}")
            return jsonify({"error": "Unauthorized App", "code": "INVALID_APP_CHECK"}), 401
    return decorated_function

# --- 2. FCM TOKEN REGISTRATION ---
@firebase_bp.route('/register-token', methods=['POST'])
@jwt_required()
def register_fcm_token():
    """Saves the FCM token to the user's profile for later messaging"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    token = data.get('fcm_token')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 400

    user = User.query.get(user_id)
    if user:
        user.fcm_token = token
        db.session.commit()
        return jsonify({'success': True, 'message': 'FCM Token updated'}), 200
    
    return jsonify({'error': 'User not found'}), 404

# --- 3. APP CHECK VERIFICATION ENDPOINT ---
@firebase_bp.route('/verify-device', methods=['POST'])
@jwt_required()
@require_app_check # <--- This validates the header
def verify_device_status():
    """
    If the request reaches here, the App Check token was valid.
    We mark the user as trusted in the DB.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user:
        user.last_app_check_at = datetime.utcnow()
        user.is_device_trusted = True
        db.session.commit()
        return jsonify({'success': True, 'is_trusted': True}), 200
        
    return jsonify({'error': 'User not found'}), 404