from extensions import db
from datetime import datetime

class BlockedDate(db.Model):
    """Dates when property cannot be booked"""
    __tablename__ = 'blocked_dates'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    blocked_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255))  # Optional: why it's blocked
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'blocked_date': self.blocked_date.isoformat(),
            'reason': self.reason,
        }