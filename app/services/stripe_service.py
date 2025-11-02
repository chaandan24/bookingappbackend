"""
Stripe Payment Service
Handles all Stripe payment operations
"""

import stripe
from flask import current_app
from datetime import datetime


class StripeService:
    """Service for handling Stripe payments"""
    
    @staticmethod
    def initialize():
        """Initialize Stripe with API key"""
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    
    @staticmethod
    def create_payment_intent(amount, currency='usd', metadata=None):
        """
        Create a Stripe Payment Intent
        
        Args:
            amount: Amount in cents (e.g., 15000 for $150.00)
            currency: Currency code (default: 'usd')
            metadata: Dict of metadata to attach to payment
        
        Returns:
            Payment Intent object
        """
        try:
            StripeService.initialize()
            
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True},
            )
            
            return {
                'success': True,
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': amount,
                'currency': currency
            }
        except stripe.error.StripeError as e:
            current_app.logger.error(f'Stripe error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def confirm_payment(payment_intent_id):
        """
        Confirm a payment intent
        
        Args:
            payment_intent_id: The Payment Intent ID
        
        Returns:
            Payment Intent status
        """
        try:
            StripeService.initialize()
            
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'success': True,
                'status': payment_intent.status,
                'amount': payment_intent.amount / 100,  # Convert from cents
                'currency': payment_intent.currency
            }
        except stripe.error.StripeError as e:
            current_app.logger.error(f'Stripe error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_refund(payment_intent_id, amount=None, reason=None):
        """
        Create a refund for a payment
        
        Args:
            payment_intent_id: The Payment Intent ID to refund
            amount: Amount to refund in dollars (None for full refund)
            reason: Reason for refund
        
        Returns:
            Refund object
        """
        try:
            StripeService.initialize()
            
            refund_params = {
                'payment_intent': payment_intent_id,
            }
            
            if amount:
                refund_params['amount'] = int(amount * 100)  # Convert to cents
            
            if reason:
                refund_params['reason'] = reason
            
            refund = stripe.Refund.create(**refund_params)
            
            return {
                'success': True,
                'refund_id': refund.id,
                'amount': refund.amount / 100,
                'status': refund.status
            }
        except stripe.error.StripeError as e:
            current_app.logger.error(f'Stripe error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_customer(email, name, metadata=None):
        """
        Create a Stripe customer
        
        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata
        
        Returns:
            Customer object
        """
        try:
            StripeService.initialize()
            
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            
            return {
                'success': True,
                'customer_id': customer.id,
                'email': customer.email
            }
        except stripe.error.StripeError as e:
            current_app.logger.error(f'Stripe error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def verify_webhook_signature(payload, signature, webhook_secret):
        """
        Verify Stripe webhook signature
        
        Args:
            payload: Request body
            signature: Stripe signature header
            webhook_secret: Webhook secret from Stripe dashboard
        
        Returns:
            Event object if valid, None if invalid
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return event
        except ValueError as e:
            # Invalid payload
            current_app.logger.error(f'Invalid payload: {str(e)}')
            return None
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            current_app.logger.error(f'Invalid signature: {str(e)}')
            return None
    
    @staticmethod
    def handle_payment_success(payment_intent):
        """
        Handle successful payment webhook
        
        Args:
            payment_intent: Payment Intent object from webhook
        
        Returns:
            Processing result
        """
        # Extract booking information from metadata
        metadata = payment_intent.get('metadata', {})
        booking_id = metadata.get('booking_id')
        
        if not booking_id:
            return {'success': False, 'error': 'No booking_id in metadata'}
        
        # Import here to avoid circular imports
        from app.models.booking import Booking, BookingStatus
        from extensions import db
        
        # Update booking status
        booking = Booking.query.get(booking_id)
        if booking:
            booking.payment_status = 'succeeded'
            booking.payment_intent_id = payment_intent['id']
            booking.status = BookingStatus.CONFIRMED
            db.session.commit()
            
            return {'success': True, 'booking_id': booking_id}
        
        return {'success': False, 'error': 'Booking not found'}
    
    @staticmethod
    def handle_payment_failed(payment_intent):
        """
        Handle failed payment webhook
        
        Args:
            payment_intent: Payment Intent object from webhook
        
        Returns:
            Processing result
        """
        metadata = payment_intent.get('metadata', {})
        booking_id = metadata.get('booking_id')
        
        if not booking_id:
            return {'success': False, 'error': 'No booking_id in metadata'}
        
        from app.models.booking import Booking, BookingStatus
        from extensions import db
        
        # Update booking status
        booking = Booking.query.get(booking_id)
        if booking:
            booking.payment_status = 'failed'
            booking.status = BookingStatus.CANCELLED
            db.session.commit()
            
            return {'success': True, 'booking_id': booking_id}
        
        return {'success': False, 'error': 'Booking not found'}
