"""
Payment API Routes for Flask
Add these routes to your Flask app
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import os
from app.services.safepay_service import SafepayService

# Import your models and auth decorator
# from app.models import Booking, Payment, User
# from app.auth import token_required

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


@payments_bp.route('/safepay/create-session', methods=['POST'])
# @token_required
def create_safepay_session():
    data = request.get_json()
    amount = data.get('amount')
    
    if not amount:
        return jsonify({'error': 'Amount is required'}), 400

    service = SafepayService()
    
    try:
        # Get the tokens specifically for Mobile SDK
        tokens = service.create_payment_tracker(amount=amount)
        
        return jsonify({
            'success': True,
            'tracker': tokens['tracker'],
            'tbt': tokens['tbt']
        })
    except Exception as e:
        print(f"Safepay Error: {e}") # Log the error
        return jsonify({'success': False, 'error': str(e)}), 500