import requests
from flask import current_app

class SafepayService:
    def __init__(self):
        # Determine environment URL
        env = current_app.config.get('SAFEPAY_ENVIRONMENT', 'sandbox')
        
        # 1. Define Base URL (Ensure no trailing slash to prevent double-slash errors)
        base = "https://sandbox.api.getsafepay.com" if env == 'sandbox' else "https://api.getsafepay.com"
        self.base_url = base.rstrip('/') # Safety cleanup
        
        self.api_key = current_app.config.get('SAFEPAY_API_KEY')
        self.secret_key = current_app.config.get('SAFEPAY_V1_SECRET') 
        self.webhook_secret = current_app.config.get('SAFEPAY_WEBHOOK_SECRET')
        
        print(f"DEBUG: Service initialized with URL: {self.base_url}")

    def get_auth_token(self, amount, currency="PKR"):
        """
        Step 1: Get the Time-Based Token (TBT).
        """
        url = f"{self.base_url}/client/passport/v1/token"
        headers = {
            "X-SFPY-MERCHANT-SECRET": self.secret_key,
            "Content-Type": 'application/json'
        }
        
        payload = {
            "amount": amount,
            "currency": currency,
            "client": self.api_key,
            "environment": env_setting  # 👈 ADD THIS FIELD
        }
        print(f"DEBUG: Requesting TBT from {url}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            json_data = response.json()
            data = json_data.get('data')
            
            # 👇 FIX: Handle cases where 'data' is just the string token
            if isinstance(data, str):
                return data
            elif isinstance(data, dict) and 'token' in data:
                return data['token']
            else:
                # Debug print if structure is totally unexpected
                print(f"DEBUG: Unexpected TBT Response: {json_data}")
                raise Exception(f"Invalid TBT structure: {json_data}")
        
        raise Exception(f"Safepay TBT Error {response.status_code}: {response.text}")

    def create_payment_tracker(self, amount, currency="PKR"):
        """
        Step 2: Initialize the Order to get the Tracker.
        """
        # We need a TBT to create the order
        tbt = self.get_auth_token()
        print(f"DEBUG: TBT Received: {tbt[:10]}...") 
        
        url = f"{self.base_url}/order/v1/init"
        headers = {
            "Authorization": f"Bearer {tbt}", 
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": amount,
            "currency": currency,
            "client": self.api_key
        }
        
        print(f"DEBUG: Creating Tracker at {url}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            json_data = response.json()
            data = json_data.get('data')
            
            # 👇 FIX: Handle cases where 'data' is just the string token
            tracker = ""
            if isinstance(data, str):
                tracker = data
            elif isinstance(data, dict) and 'token' in data:
                tracker = data['token']
            else:
                print(f"DEBUG: Unexpected Tracker Response: {json_data}")
                raise Exception(f"Invalid Tracker structure: {json_data}")

            return {
                "tracker": tracker,
                "tbt": tbt
            }
            
        raise Exception(f"Safepay Tracker Error {response.status_code}: {response.text}")

    def verify_webhook(self, data, signature):
        """
        Verifies the webhook signature.
        """
        from safepay_python.safepay import Safepay
        env = Safepay({
            "environment": current_app.config.get('SAFEPAY_ENVIRONMENT', 'sandbox'),
            "apiKey": self.api_key,
            "v1Secret": self.secret_key,
            "webhookSecret": self.webhook_secret,
        })
        return env.is_webhook_valid({"x-sfpy-signature": signature}, {"data": data})