"""
Payment API Routes for Flask
Add these routes to your Flask app
"""

from flask import Blueprint, request, jsonify, current_app
from app.services.safepay_service import SafepayService
from app.models.booking import Booking, BookingStatus # Import your Booking model
from extensions import db # Import db to save changes
from app.models.card_token import CardToken

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


@payments_bp.route('/safepay/create-session', methods=['POST'])
def create_safepay_session():
    data = request.get_json()
    amount = data.get('amount')
    booking_id = data.get('booking_id')
    
    if not amount or not booking_id:
        return jsonify({'error': 'Amount and booking_id required'}), 400

    booking = Booking.query.get(booking_id)
    if not booking:
         return jsonify({'error': 'Booking not found'}), 404

    service = SafepayService()
    
    try:
        # 1. Create v3 Tracker
        result = service.create_payment_tracker(amount=amount)
        tracker = result['tracker']
        
        # 2. Save Tracker to DB
        booking.payment_intent_id = tracker
        db.session.commit()

        return jsonify({
            'success': True,
            'tracker': tracker
        })
    except Exception as e:
        print(f"Safepay Init Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@payments_bp.route('/safepay/process', methods=['POST'])
def process_payment():
    data = request.get_json()
    tracker = data.get('tracker')
    
    # We now expect a TOKEN, not raw card data
    card_token = data.get('cardToken') 
    
    billing_data = data.get('billing', {})
    
    if not tracker or not card_token:
        return jsonify({'error': 'Missing tracker or card token'}), 400

    service = SafepayService()
    
    try:
        response = service.process_native_payment(tracker, card_token, billing_data)
        return jsonify({'success': True, 'data': response})
    except Exception as e:
        print(f"Payment Process Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
