from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from extensions import db, socketio
from app.models.message import Message, Conversation
from datetime import datetime
from functools import wraps
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

messaging_bp = Blueprint('messaging', __name__)

# ============================================
# Socket.IO JWT Authentication Helper
# ============================================
def socket_jwt_required(f):
    """Custom decorator for Socket.IO events that need authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Get token from socket auth or query params
            token = None
            
            # Try auth object first (set via OptionBuilder().setAuth())
            if hasattr(request, 'namespace') and hasattr(request.namespace, 'auth'):
                token = request.namespace.auth.get('token')
            
            # Fallback to socket handshake auth
            if not token and hasattr(request, 'sid'):
                from flask import current_app
                auth = current_app.extensions['socketio'].server.get_session(request.sid).get('auth')
                if auth:
                    token = auth.get('token')
            
            if not token:
                emit('error', {'message': 'Authentication required'})
                return
            
            # Decode and verify token
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            
            if not user_id:
                emit('error', {'message': 'Invalid token'})
                return
            
            # Add user_id to kwargs for the handler
            kwargs['user_id'] = user_id
            return f(*args, **kwargs)
            
        except Exception as e:
            print(f"Socket auth error: {e}")
            emit('error', {'message': 'Authentication failed'})
            return
    
    return decorated


# ============================================
# REST endpoints for message history
# ============================================
@messaging_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    user_id = get_jwt_identity()
    convos = Conversation.query.filter(
        (Conversation.user1_id == user_id) | (Conversation.user2_id == user_id)
    ).order_by(Conversation.updated_at.desc()).all()
    return jsonify({'conversations': [c.to_dict() for c in convos]})


@messaging_bp.route('/conversations/<int:convo_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(convo_id):
    user_id = get_jwt_identity()
    convo = Conversation.query.get_or_404(convo_id)
    
    if user_id not in [convo.user1_id, convo.user2_id]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    messages = Message.query.filter_by(conversation_id=convo_id)\
        .order_by(Message.created_at.asc()).all()
    return jsonify({'messages': [m.to_dict() for m in messages]})


@messaging_bp.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    other_user_id = data.get('user_id')
    property_id = data.get('property_id')
    
    if not other_user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    if current_user_id == other_user_id:
        return jsonify({'error': 'Cannot message yourself'}), 400
    
    # Check if conversation already exists
    existing = Conversation.query.filter(
        db.or_(
            db.and_(Conversation.user1_id == current_user_id, Conversation.user2_id == other_user_id),
            db.and_(Conversation.user1_id == other_user_id, Conversation.user2_id == current_user_id)
        ),
        Conversation.property_id == property_id
    ).first()
    
    if existing:
        return jsonify({'conversation': existing.to_dict()}), 200
    
    # Create new conversation
    conversation = Conversation(
        user1_id=current_user_id,
        user2_id=other_user_id,
        property_id=property_id
    )
    db.session.add(conversation)
    db.session.commit()
    
    return jsonify({'conversation': conversation.to_dict()}), 201


# ============================================
# WebSocket events
# ============================================
@socketio.on('connect')
def handle_connect():
    """Handle client connection - store auth for later use"""
    logger.info(f"[connect] Client connected: {request.sid}")
    logger.debug(f"[connect] Args: {request.args}")
    logger.debug(f"[connect] Headers: {dict(request.headers)}")
    
    emit('connected', {'status': 'ok'})


@socketio.on('join')
def handle_join(data):
    """Join a conversation room"""
    logger.info(f"[join] Data received: {data}")
    room = f"convo_{data['conversation_id']}"
    join_room(room)
    emit('joined', {'room': room})
    logger.info(f"[join] Client {request.sid} joined {room}")


@socketio.on('leave')
def handle_leave(data):
    """Leave a conversation room"""
    room = f"convo_{data['conversation_id']}"
    leave_room(room)
    print(f"Client {request.sid} left {room}")


@socketio.on('send_message')
def handle_message(data):
    """
    Handle incoming message.
    
    Expected data:
    {
        'conversation_id': int,
        'sender_id': int,
        'content': str
    }
    """
    logger.info(f"[send_message] Received data: {data}")
    
    try:
        convo_id = data.get('conversation_id')
        sender_id = data.get('sender_id')
        content = data.get('content')
        
        logger.debug(f"[send_message] convo_id={convo_id}, sender_id={sender_id}, content={content[:50] if content else None}")
        
        # Validate required fields
        if not all([convo_id, sender_id, content]):
            logger.error(f"[send_message] Missing fields - convo_id={convo_id}, sender_id={sender_id}, content={bool(content)}")
            emit('error', {'message': 'Missing required fields'})
            return
        
        # Verify conversation exists and user is participant
        convo = Conversation.query.get(convo_id)
        if not convo:
            logger.error(f"[send_message] Conversation {convo_id} not found")
            emit('error', {'message': 'Conversation not found'})
            return
        
        if sender_id not in [convo.user1_id, convo.user2_id]:
            logger.error(f"[send_message] Unauthorized - sender_id={sender_id} not in [{convo.user1_id}, {convo.user2_id}]")
            emit('error', {'message': 'Unauthorized'})
            return
        
        # Save to database
        message = Message(
            conversation_id=convo_id,
            sender_id=sender_id,
            content=content
        )
        db.session.add(message)
        
        # Update conversation timestamp
        convo.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"[send_message] Message saved with id={message.id}")
        
        # Broadcast to room (this is what Flutter is waiting for!)
        room = f"convo_{convo_id}"
        message_dict = message.to_dict()
        logger.info(f"[send_message] Emitting new_message to room {room}: {message_dict}")
        emit('new_message', message_dict, room=room)
        
        logger.info(f"[send_message] SUCCESS - Message sent in {room}")
        
    except Exception as e:
        logger.error(f"[send_message] EXCEPTION: {e}")
        logger.error(f"[send_message] Traceback: {traceback.format_exc()}")
        db.session.rollback()
        emit('error', {'message': 'Failed to send message', 'details': str(e)})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnect"""
    print(f"Client disconnected: {request.sid}")