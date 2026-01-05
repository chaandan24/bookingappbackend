"""
Payment API Routes for Flask
Add these routes to your Flask app
"""

from flask import Blueprint, request, jsonify, current_app
from app.services.safepay_service import SafepayService
from app.models.booking import Booking, BookingStatus # Import your Booking model
from extensions import db # Import db to save changes

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


# --- ENDPOINT 1: Start the Payment (Frontend calls this) ---
@payments_bp.route('/safepay/create-session', methods=['POST'])
def create_safepay_session():
    data = request.get_json()
    amount = data.get('amount')
    booking_id = data.get('booking_id') # REQUIRED: We need this to link payment
    
    if not amount or not booking_id:
        return jsonify({'error': 'Amount and booking_id are required'}), 400

    # 1. Fetch the Booking
    booking = Booking.query.get(booking_id)
    if not booking:
         return jsonify({'error': 'Booking not found'}), 404

    service = SafepayService()
    
    try:
        # 2. Generate Tokens
        tokens = service.create_payment_tracker(amount=amount)
        
        # 3. SAVE THE TRACKER TO YOUR BOOKING MODEL
        # We use 'payment_intent_id' to store the Safepay Tracker Token.
        # This is the "Link" that allows the webhook to find this booking later.
        booking.payment_intent_id = tokens['tracker']
        db.session.commit()

        return jsonify({
            'success': True,
            'tracker': tokens['tracker'],
            'tbt': tokens['tbt']
        })
    except Exception as e:
        print(f"Safepay Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# --- ENDPOINT 2: Listen for Success (Safepay calls this) ---
@payments_bp.route('/safepay/webhook', methods=['POST'])
def safepay_webhook():
    """
    Safepay sends a notification here when payment is complete.
    """
    # 1. Get the signature from headers
    signature = request.headers.get('X-SFPY-SIGNATURE')
    if not signature:
        return jsonify({'error': 'No signature'}), 403

    # 2. Get the raw data
    payload = request.get_data()
    service = SafepayService()

    # 3. Verify the notification is actually from Safepay
    # (Ensure your SafepayService has the verify_webhook method we discussed)
    try:
        if not service.verify_webhook(payload, signature):
             return jsonify({'error': 'Invalid signature'}), 403
    except Exception as e:
        # If verify_webhook fails (e.g. missing library), log it
        print(f"Webhook Verification Error: {e}")
        # For development, you might temporarily pass, but strictly return 403 in prod
        return jsonify({'error': 'Verification failed'}), 403

    # 4. Process the data
    data = request.get_json()
    event_type = data.get('type') # Safepay event type
    payload_data = data.get('data', {})
    
    # The 'token' in the webhook data is the same 'tracker' we saved earlier
    tracker_token = payload_data.get('token') 

    print(f"Received Webhook: {event_type} for Tracker {tracker_token}")

    if event_type == 'payment.succeeded':
        # 5. FIND THE BOOKING using the stored payment_intent_id
        if tracker_token:
            booking = Booking.query.filter_by(payment_intent_id=tracker_token).first()
            
            if booking:
                print(f"Marking Booking {booking.id} as CONFIRMED")
                
                # Update Booking Status
                booking.payment_status = 'paid'
                booking.status = BookingStatus.CONFIRMED
                
                # Commit changes
                db.session.commit()
                return jsonify({'success': True, 'message': 'Booking confirmed'}), 200
            else:
                print(f"Error: No booking found for tracker {tracker_token}")
                return jsonify({'error': 'Booking not found'}), 404

    return jsonify({'success': True}), 200