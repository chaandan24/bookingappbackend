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
        last_message = self.messages.order_by(Message.created_at.desc()).first()
        
        # 2. Get total count of messages in this conversation
        total_messages = self.messages.count()
        
        # 3. Calculate unread count for the specific user requesting the data
        unread_count = 0
        if current_user_id:
            if current_user_id == self.user1_id:
                unread_count = total_messages - self.user1_read_count
            elif current_user_id == self.user2_id:
                unread_count = total_messages - self.user2_read_count
        
        # Safety check: ensure count never goes below 0
        if unread_count < 0:
            unread_count = 0
        return {
            'id': self.id,
            'user1': self.user1.to_dict(),
            'user2': self.user2.to_dict(),
            'property_id': self.property_id,
            'updated_at': self.updated_at.isoformat(),
            'last_message': last_message.to_dict() if last_message else None,
            'messages': [m.to_dict() for m in self.messages.order_by(Message.created_at.desc()).all()]
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