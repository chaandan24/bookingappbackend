from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import firebase_admin
from firebase_admin import credentials, messaging
from app.models import User

notifications_bp = Blueprint('notifications', __name__)

# Initialize Firebase (add your credentials JSON path)
cred = credentials.Certificate('path/to/your/firebase-key.json')
firebase_admin.initialize_app(cred)

@notifications_bp.route('/register-token', methods=['POST'])
@jwt_required()
def register_device_token():
    """Store user's FCM token"""
    user_id = get_jwt_identity()
    data = request.get_json()
    fcm_token = data.get('token')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.fcm_token = fcm_token
    db.session.commit()
    
    return jsonify({'message': 'Token registered'}), 200

@notifications_bp.route('/send', methods=['POST'])
@jwt_required()
def send_notification():
    """Send notification to a user"""
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    body = data.get('body')
    
    user = User.query.get(user_id)
    if not user or not user.fcm_token:
        return jsonify({'error': 'User or token not found'}), 404
    
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=user.fcm_token
    )
    
    response = messaging.send(message)
    return jsonify({'message_id': response}), 200