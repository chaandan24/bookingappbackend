"""
Script to make a user admin
Usage: python scripts/make_admin.py user@example.com
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import
from app import create_app
from extensions import db
from app.models.user import User

def make_admin(email):
    """Make a user admin by email"""
    app = create_app()
    
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found")
            print(f"\n💡 Available users:")
            users = User.query.all()
            for u in users:
                print(f"   - {u.email} ({u.full_name})")
            return False
        
        if user.is_admin:
            print(f"✓ User '{email}' is already an admin")
            return True
        
        user.is_admin = True
        db.session.commit()
        
        print(f"✅ Successfully made '{email}' an admin")
        print(f"   Name: {user.full_name}")
        print(f"   Username: {user.username}")
        print(f"   Role: {user.role}")
        print(f"   Is Admin: {user.is_admin}")
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/make_admin.py <email>")
        print("Example: python scripts/make_admin.py admin@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    make_admin(email)