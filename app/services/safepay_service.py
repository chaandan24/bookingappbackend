import requests
from flask import current_app

class SafepayService:
    def __init__(self):
        # Determine environment URL
        env = current_app.config.get('SAFEPAY_ENVIRONMENT', 'sandbox')
        self.base_url = "https://sandbox.api.getsafepay.com/" if env == 'sandbox' else "https://api.getsafepay.com/"
        
        self.api_key = current_app.config.get('SAFEPAY_API_KEY')
        self.secret_key = current_app.config.get('SAFEPAY_V1_SECRET') 
        self.webhook_secret = current_app.config.get('SAFEPAY_WEBHOOK_SECRET')

    def get_auth_token(self):
        """
        Step 1: Get the Time-Based Token (TBT).
        This authenticates the mobile session for a short time.
        """
        url = f"{self.base_url}/client/passport"
        headers = {
            "X-SFPY-MERCHANT-SECRET": self.secret_key
        }
        
        response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()['data']['token']
        
        raise Exception(f"Safepay TBT Error: {response.text}")

    def create_payment_tracker(self, amount, currency="PKR"):
        """
        Step 2: Initialize the Order to get the Tracker.
        """
        # We need a TBT to create the order
        tbt = self.get_auth_token()
        
        url = f"{self.base_url}/order/v1/init"
        headers = {
            "Authorization": f"Bearer {tbt}", # Authenticate with TBT
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": amount,
            "currency": currency,
            "client": self.api_key # The API Key (Public Key)
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return {
                "tracker": response.json()['data']['token'], # The order ID
                "tbt": tbt # The session token
            }
            
        raise Exception(f"Safepay Tracker Error: {response.text}")

    def verify_webhook(self, data, signature):
        """
        Verifies the webhook signature.
        (You can keep using the library for this if you prefer, or manual logic)
        """
        from safepay_python.safepay import Safepay
        env = Safepay({
            "environment": current_app.config.get('SAFEPAY_ENVIRONMENT', 'sandbox'),
            "apiKey": self.api_key,
            "v1Secret": self.secret_key,
            "webhookSecret": self.webhook_secret,
        })
        return env.is_webhook_valid({"x-sfpy-signature": signature}, {"data": data})