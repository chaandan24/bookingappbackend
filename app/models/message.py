from extensions import db
from datetime import datetime

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    messages = db.relationship('Message', backref='conversation', lazy='dynamic')
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])
    user1_read_count = db.Column(db.Integer, default=0)
    user2_read_count = db.Column(db.Integer, default=0)
    
    def to_dict(self, current_user_id=None):
        # 1. Get messages (limit to 20 for performance in list view)
        last_message = self.messages.order_by(Message.created_at.desc()).first()
        total_messages = self.messages.count()
        
        unread_count = 0
        
        if current_user_id:
            try:
                # FIX 1: Force Integer Comparison
                uid = int(current_user_id) 
                
                # FIX 2: Handle NULL values from DB (defaults to 0)
                u1_read = self.user1_read_count if self.user1_read_count is not None else 0
                u2_read = self.user2_read_count if self.user2_read_count is not None else 0

                if uid == self.user1_id:
                    unread_count = total_messages - u1_read
                elif uid == self.user2_id:
                    unread_count = total_messages - u2_read
            except Exception as e:
                print(f"Error calculating unread: {e}")

        # Safety Check
        if unread_count < 0: 
            unread_count = 0

        # FIX 3: Safe Sender Serialization (Handle Deleted Users)
        msgs_list = []
        try:
            # Only sending last message needed for the list view, 
            # but if you need all, keep this.
            msgs_list = [m.to_dict() for m in self.messages.order_by(Message.created_at.desc()).all()]
        except:
            pass

        return {
            'id': self.id,
            'user1': self.user1.to_dict() if self.user1 else None,
            'user2': self.user2.to_dict() if self.user2 else None,
            'property_id': self.property_id,
            'updated_at': self.updated_at.isoformat(),
            'last_message': last_message.to_dict() if last_message else None,
            'messages': msgs_list,
            'unread_count': unread_count
        }

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender': self.sender.to_dict(),
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }