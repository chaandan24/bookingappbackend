from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db, pusher_client
from app.models.message import Message, Conversation
from datetime import datetime
import logging
import traceback
from app.api.firebase.routes import notify_user
from app.models.user import User

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

messaging_bp = Blueprint('messaging', __name__)

# ============================================
# REST Endpoints
# ============================================

@messaging_bp.route('/conversations/get', methods=['GET'])
@jwt_required()
def get_conversations():
    user_id = get_jwt_identity()
    convos = Conversation.query.filter(
        (Conversation.user1_id == user_id) | (Conversation.user2_id == user_id)
    ).order_by(Conversation.updated_at.desc()).all()
    print([c.to_dict() for c in convos])

    return jsonify({'conversations': [c.to_dict() for c in convos]})


@messaging_bp.route('/conversations/<int:convo_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(convo_id):
    user_id = int(get_jwt_identity())
    convo = Conversation.query.get_or_404(convo_id)
    
    if user_id not in [convo.user1_id, convo.user2_id]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    messages = Message.query.filter_by(conversation_id=convo_id)\
        .order_by(Message.created_at.desc()).all()
    
    return jsonify({
        'messages': [m.to_dict() for m in messages]
    })


@messaging_bp.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    other_user_id = data.get('user_id')
    property_id = data.get('property_id')
    content = data.get('content') # 1. Extract content
    
    if not other_user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    if current_user_id == other_user_id:
        return jsonify({'error': 'Cannot message yourself'}), 400
    
    # Check if conversation already exists
    conversation = Conversation.query.filter(
        db.or_(
            db.and_(Conversation.user1_id == current_user_id, Conversation.user2_id == other_user_id),
            db.and_(Conversation.user1_id == other_user_id, Conversation.user2_id == current_user_id)
        ),
        Conversation.property_id == property_id
    ).first()
    
    # If not, create it
    if not conversation:
        conversation = Conversation(
            user1_id=current_user_id,
            user2_id=other_user_id,
            property_id=property_id
        )
        db.session.add(conversation)
        db.session.commit()
    
    # 2. Logic to handle the initial message
    response_data = {'conversation': conversation.to_dict()}
    
    if content:
        new_message = Message(
            conversation_id=conversation.id,
            sender_id=current_user_id,
            content=content
        )
        db.session.add(new_message)
        db.session.commit()
        
        # 3. Add message to response so Provider can update UI
        response_data['message'] = new_message.to_dict()
        
        # Optional: Trigger Pusher event here so the receiver gets it immediately
        # pusher_client.trigger(...) 

    return jsonify(response_data), 201


@messaging_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    try:
        data = request.get_json()
        sender_id = int(get_jwt_identity())
        
        convo_id = data.get('conversation_id')
        content = data.get('content')

        if not convo_id or not content:
            return jsonify({'error': 'Missing conversation_id or content'}), 400

        convo = Conversation.query.get(convo_id)
        if not convo:
            return jsonify({'error': 'Conversation not found'}), 404

        if sender_id not in [convo.user1_id, convo.user2_id]:
            return jsonify({'error': 'Unauthorized'}), 403

        message = Message(
            conversation_id=convo_id,
            sender_id=sender_id,
            content=content
        )
        db.session.add(message)
        convo.updated_at = datetime.utcnow()
        db.session.commit()

        # Determine recipient
        recipient_id = convo.user2_id if convo.user1_id == sender_id else convo.user1_id
    
        # Get sender name for notification
        sender = User.query.get(sender_id)
        sender_name = sender.username or sender.first_name or "Someone"
    
        # Send push notification
        notify_user(
            user_id=recipient_id,
            title=sender_name,
            body=content[:100],
            data={
                "type": "message",
                "conversation_id": str(convo_id),
                "sender_id": str(sender_id)
            }
        )

        # Pusher
        try:
            channel_name = f"convo_{convo_id}"
            pusher_client.trigger(channel_name, 'new_message', message.to_dict())
            logger.info(f"Pusher event triggered on channel {channel_name}")
        except Exception as e:
            logger.error(f"Pusher Error: {e}")
            logger.error(traceback.format_exc())

        return jsonify({'message': message.to_dict()}), 201

    except Exception as e:
        logger.error(f"Send Message Error: {e}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Failed to send message'}), 500