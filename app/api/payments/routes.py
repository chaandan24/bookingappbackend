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
# @token_required # Uncomment to require login
def create_safepay_session():
    data = request.get_json()
    amount = data.get('amount')
    booking_id = data.get('booking_id')
    
    if not amount:
        return jsonify({'error': 'Amount is required'}), 400

    service = SafepayService()
    
    try:
        # These URLs should be deep links to your app or a success page on your website
        # Example: "myapp://payment-success" or "https://your-site.com/payment/success"
        checkout_url = service.create_checkout_link(
            amount=amount,
            order_id=booking_id,
            cancel_url="https://your-website.com/payment/cancel", 
            redirect_url="https://your-website.com/payment/success"
        )
        
        return jsonify({
            'success': True, 
            'checkout_url': checkout_url
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/safepay/webhook', methods=['POST'])
def safepay_webhook():
    signature = request.headers.get('x-sfpy-signature')
    data = request.get_data() # Raw data is needed for verification
    
    service = SafepayService()
    
    if service.verify_webhook(data, signature):
        payload = request.get_json()
        # 1. Extract status and order_id
        # 2. Update your database (e.g., mark booking as paid)
        print(f"SafePay Payment Processed: {payload}")
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'error': 'Invalid Signature'}), 403