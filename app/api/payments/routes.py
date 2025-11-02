"""
Payments Routes with Stripe Integration
"""

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from app.models.booking import Booking, BookingStatus
from app.services.stripe_service import StripeService
from app.services.email_service import EmailService

payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/create-payment-intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    """Create Stripe payment intent for booking"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate booking_id
        booking_id = data.get('booking_id')
        if not booking_id:
            return jsonify({'error': 'booking_id is required'}), 400
        
        # Get booking
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Verify user owns this booking
        if booking.guest_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if already paid
        if booking.payment_status == 'succeeded':
            return jsonify({'error': 'Booking already paid'}), 400
        
        # Create payment intent
        result = StripeService.create_payment_intent(
            amount=float(booking.total_price),
            currency='usd',
            metadata={
                'booking_id': booking.id,
                'property_id': booking.property_id,
                'guest_id': booking.guest_id
            }
        )
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Payment creation failed')}), 500
        
        # Update booking with payment intent ID
        booking.payment_intent_id = result['payment_intent_id']
        booking.payment_status = 'pending'
        db.session.commit()
        
        return jsonify({
            'client_secret': result['client_secret'],
            'payment_intent_id': result['payment_intent_id'],
            'amount': result['amount'],
            'currency': result['currency'],
            'booking_id': booking.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Payment intent creation error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@payments_bp.route('/confirm-payment', methods=['POST'])
@jwt_required()
def confirm_payment():
    """Confirm payment status"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        payment_intent_id = data.get('payment_intent_id')
        if not payment_intent_id:
            return jsonify({'error': 'payment_intent_id is required'}), 400
        
        # Get booking
        booking = Booking.query.filter_by(payment_intent_id=payment_intent_id).first()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Verify user owns this booking
        if booking.guest_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Confirm payment with Stripe
        result = StripeService.confirm_payment(payment_intent_id)
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Payment confirmation failed')}), 500
        
        # Update booking based on payment status
        if result['status'] == 'succeeded':
            booking.payment_status = 'succeeded'
            booking.status = BookingStatus.CONFIRMED
            db.session.commit()
            
            # Send confirmation emails
            try:
                guest = booking.guest
                property_obj = booking.property
                host = property_obj.host
                
                EmailService.send_booking_confirmation(booking, guest, property_obj, host)
                EmailService.send_booking_notification_to_host(booking, guest, property_obj, host)
            except Exception as email_error:
                current_app.logger.error(f'Email sending failed: {str(email_error)}')
            
            return jsonify({
                'message': 'Payment successful',
                'status': result['status'],
                'booking': booking.to_dict(include_property=True)
            }), 200
        else:
            booking.payment_status = result['status']
            db.session.commit()
            
            return jsonify({
                'message': 'Payment status updated',
                'status': result['status']
            }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Payment confirmation error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@payments_bp.route('/refund', methods=['POST'])
@jwt_required()
def create_refund():
    """Create a refund for a cancelled booking"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        booking_id = data.get('booking_id')
        if not booking_id:
            return jsonify({'error': 'booking_id is required'}), 400
        
        # Get booking
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Verify user is guest or host
        if booking.guest_id != current_user_id and booking.property.host_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if booking is cancelled
        if booking.status != BookingStatus.CANCELLED:
            return jsonify({'error': 'Booking is not cancelled'}), 400
        
        # Check if payment was successful
        if booking.payment_status != 'succeeded':
            return jsonify({'error': 'No successful payment to refund'}), 400
        
        # Create refund
        result = StripeService.create_refund(
            payment_intent_id=booking.payment_intent_id,
            reason='requested_by_customer'
        )
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Refund creation failed')}), 500
        
        # Update booking
        booking.payment_status = 'refunded'
        db.session.commit()
        
        return jsonify({
            'message': 'Refund created successfully',
            'refund_id': result['refund_id'],
            'amount': result['amount'],
            'status': result['status']
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Refund creation error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        
        if not webhook_secret:
            return jsonify({'error': 'Webhook secret not configured'}), 500
        
        # Verify webhook signature
        event = StripeService.verify_webhook_signature(payload, sig_header, webhook_secret)
        
        if not event:
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Handle different event types
        event_type = event['type']
        
        if event_type == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            result = StripeService.handle_payment_success(payment_intent)
            
            if result['success']:
                # Send confirmation emails
                try:
                    booking_id = result.get('booking_id')
                    booking = Booking.query.get(booking_id)
                    if booking:
                        guest = booking.guest
                        property_obj = booking.property
                        host = property_obj.host
                        
                        EmailService.send_booking_confirmation(booking, guest, property_obj, host)
                        EmailService.send_booking_notification_to_host(booking, guest, property_obj, host)
                except Exception as email_error:
                    current_app.logger.error(f'Email sending failed: {str(email_error)}')
        
        elif event_type == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            StripeService.handle_payment_failed(payment_intent)
        
        return jsonify({'received': True}), 200
        
    except Exception as e:
        current_app.logger.error(f'Webhook error: {str(e)}')
        return jsonify({'error': str(e)}), 500
