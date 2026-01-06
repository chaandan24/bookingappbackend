from extensions import db
from datetime import datetime

class CardToken(db.Model):
    __tablename__ = 'card_tokens'

    id = db.Column(db.Integer, primary_key=True)
    
    # Link to your User model (Assuming you have user authentication)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # The Safe Token from Basis Theory (e.g., "token_123...")
    # We use this to charge the card, but it's useless to hackers without your BT Private Key.
    token_id = db.Column(db.String(100), nullable=False)
    
    # The Display Data (Safe to store plain text)
    card_mask = db.Column(db.String(4), nullable=False) # Last 4 digits: "4242"
    card_type = db.Column(db.String(20), nullable=True) # "Visa", "MasterCard"
    expiry_month = db.Column(db.String(2), nullable=False)
    expiry_year = db.Column(db.String(4), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'token_id': self.token_id,
            'card_mask': self.card_mask,
            'card_type': self.card_type,
            'expiry_month': self.expiry_month,
            'expiry_year': self.expiry_year
        }