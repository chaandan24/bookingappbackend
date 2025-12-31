from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db, socketio
from app.models.message import Message, Conversation
from datetime import datetime

messaging_bp = Blueprint('messaging', __name__)

# REST endpoints for message history
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


# WebSocket events
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('join')
def handle_join(data):
    """Join a conversation room"""
    room = f"convo_{data['conversation_id']}"
    join_room(room)
    emit('joined', {'room': room})

@socketio.on('leave')
def handle_leave(data):
    room = f"convo_{data['conversation_id']}"
    leave_room(room)

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming message"""
    convo_id = data['conversation_id']
    sender_id = data['sender_id']
    content = data['content']
    
    # Save to database
    message = Message(
        conversation_id=convo_id,
        sender_id=sender_id,
        content=content
    )
    db.session.add(message)
    
    # Update conversation timestamp
    convo = Conversation.query.get(convo_id)
    convo.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Broadcast to room
    room = f"convo_{convo_id}"
    emit('new_message', message.to_dict(), room=room)