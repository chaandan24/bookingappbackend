from safepay_python.safepay import Safepay
from flask import current_app

class SafepayService:
    def __init__(self):
        self.env = Safepay({
            "environment": current_app.config.get('SAFEPAY_ENVIRONMENT', 'sandbox'),
            "apiKey": current_app.config.get('SAFEPAY_API_KEY'),
            "v1Secret": current_app.config.get('SAFEPAY_V1_SECRET'),
            "webhookSecret": current_app.config.get('SAFEPAY_WEBHOOK_SECRET'),
        })

    def create_checkout_link(self, amount, currency="PKR", order_id=None, cancel_url=None, redirect_url=None):
        """
        Creates a payment session and returns the checkout URL.
        """
        # 1. Initialize Payment to get the Tracker (Token)
        payment_response = self.env.set_payment_details({
            "amount": amount,
            "currency": currency
        })
        
        token = payment_response['data']['token']

        # 2. Generate the Checkout URL
        # For mobile apps, we set source="mobile" to optimize the view
        checkout_url = self.env.get_checkout_url({
            "beacon": token,
            "cancelUrl": cancel_url,
            "orderId": order_id,
            "redirectUrl": redirect_url,
            "source": "mobile", 
            "webhooks": True,
        })
        
        return checkout_url

    def verify_webhook(self, data, signature):
        """
        Verifies the webhook signature from SafePay
        """
        return self.env.is_webhook_valid(
            {"x-sfpy-signature": signature}, 
            {"data": data}
        )