"""
Payment API Routes for Flask
Add these routes to your Flask app
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import os

# Import your models and auth decorator
# from app.models import Booking, Payment, User
# from app.auth import token_required

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


def get_payment_service():
    """Get configured payment service instance"""
    from app.services.xpay_service import XPayService
    
    return XPayService(
        public_key=current_app.config['XPAY_PUBLIC_KEY'],
        hmac_key=current_app.config['XPAY_HMAC_KEY'],
        account_id=current_app.config['XPAY_ACCOUNT_ID'],
        environment=current_app.config.get('XPAY_ENVIRONMENT', 'staging')
    )


@payments_bp.route('/create-intent', methods=['POST'])
# @token_required  # Uncomment when you have auth
def create_payment_intent():
    """
    Create payment intent for Flutter SDK.
    
    Request:
    {
        "booking_id": "123",
        "amount": 5000.00,
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "customer_phone": "+923001234567"
    }
    
    Response:
    {
        "success": true,
        "client_secret": "pi_secret_xxx",
        "encryption_key": "enc_key_xxx",
        "pi_id": "pi_xxx"
    }
    
    Flutter SDK usage:
    ```dart
    var response = await controller.confirmPayment(
        customerName: "John Doe",
        clientSecret: response['client_secret'],
        encryptionKeys: response['encryption_key']
    );
    ```
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    
    # Validate required fields
    required_fields = ['booking_id', 'amount']
    for field in required_fields:
        if field not in data:
            return jsonify({
                "success": False, 
                "error": f"Missing required field: {field}"
            }), 400
    
    # Optional: Verify booking exists and belongs to user
    # booking = Booking.query.get(data['booking_id'])
    # if not booking:
    #     return jsonify({"success": False, "error": "Booking not found"}), 404
    
    service = get_payment_service()
    
    result = service.create_payment_intent(
        amount=float(data['amount']),
        currency=data.get('currency', 'PKR'),
        order_id=str(data['booking_id']),
        customer_name=data.get('customer_name'),
        customer_email=data.get('customer_email'),
        customer_phone=data.get('customer_phone'),
        metadata={
            "booking_id": data['booking_id'],
            "app": "DossDown"
        }
    )
    
    if not result['success']:
        return jsonify({
            "success": False,
            "error": result.get('error', 'Failed to create payment intent')
        }), 500
    
    # Optional: Store payment intent in database
    # payment = Payment(
    #     booking_id=data['booking_id'],
    #     pi_id=result['pi_id'],
    #     amount=data['amount'],
    #     status='pending'
    # )
    # db.session.add(payment)
    # db.session.commit()
    
    return jsonify({
        "success": True,
        "client_secret": result['pi_client_secret'],
        "encryption_key": result['encryption_key'],
        "pi_id": result['pi_id']
    })


@payments_bp.route('/status/<pi_id>', methods=['GET'])
# @token_required
def get_payment_status(pi_id):
    """
    Get payment status by payment intent ID.
    
    Response:
    {
        "success": true,
        "status": "succeeded",
        "amount": 5000,
        "currency": "PKR"
    }
    """
    service = get_payment_service()
    result = service.get_payment_status(pi_id)
    
    if not result['success']:
        return jsonify({
            "success": False,
            "error": result.get('error', 'Failed to get payment status')
        }), 500
    
    return jsonify({
        "success": True,
        "data": result['data']
    })


@payments_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """
    Handle payment webhook notifications.
    
    Configure webhook URL in dashboard:
    https://yourdomain.com/api/payments/webhook
    """
    payload = request.get_data()
    signature = request.headers.get('x-signature', '')
    
    # Verify signature
    webhook_secret = current_app.config.get('XPAY_WEBHOOK_SECRET')
    if webhook_secret:
        service = get_payment_service()
        if not service.verify_webhook_signature(payload, signature, webhook_secret):
            return jsonify({"error": "Invalid signature"}), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data"}), 400
    
    event_type = data.get('event_type') or data.get('status')
    pi_id = data.get('pi_id') or data.get('payment_intent_id')
    
    print(f"Payment Webhook: {event_type} for {pi_id}")
    
    # Handle different event types
    if event_type in ['payment.succeeded', 'succeeded', 'SUCCESSFUL']:
        # Update booking status
        # payment = Payment.query.filter_by(pi_id=pi_id).first()
        # if payment:
        #     payment.status = 'completed'
        #     payment.booking.status = 'confirmed'
        #     db.session.commit()
        pass
    
    elif event_type in ['payment.failed', 'failed', 'FAILED']:
        # Handle failed payment
        # payment = Payment.query.filter_by(pi_id=pi_id).first()
        # if payment:
        #     payment.status = 'failed'
        #     db.session.commit()
        pass
    
    return jsonify({"received": True})


# Add to your Flask app:
# app.register_blueprint(payments_bp)