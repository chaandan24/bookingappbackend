import requests
from flask import current_app

class SafepayService:
    def __init__(self):
        # 1. Setup Base URL
        env = current_app.config.get('SAFEPAY_ENVIRONMENT', 'sandbox')
        base = "https://sandbox.api.getsafepay.com" if env == 'sandbox' else "https://api.getsafepay.com"
        self.base_url = base.rstrip('/')
        
        # 2. Load Keys
        self.api_key = current_app.config.get('SAFEPAY_API_KEY')      # Public Key
        self.secret_key = current_app.config.get('SAFEPAY_V1_SECRET') # Secret Key
        self.webhook_secret = current_app.config.get('SAFEPAY_WEBHOOK_SECRET')

        self.bt_private_key = current_app.config.get('BASIS_THEORY_PRIVATE_KEY')

    def create_payment_tracker(self, amount, currency="PKR"):
        """
        Step 1: Create v3 Tracker (Same as before)
        """
        url = f"{self.base_url}/order/payments/v3/"
        headers = {
            "Content-Type": "application/json",
            "X-SFPY-MERCHANT-SECRET": self.secret_key
        }
        payload = {
            "merchant_api_key": self.api_key,
            "intent": "CYBERSOURCE",
            "mode": "payment",
            "currency": currency,
            "amount": int(amount * 100) if currency == "PKR" else amount,
            "entry_mode": "raw"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json().get('data', {})
            tracker = data.get('token') if isinstance(data, dict) else data
            return {"tracker": tracker}
            
        raise Exception(f"Safepay Init Error: {response.text}")

    def process_native_payment(self, tracker, card_token, billing_details):
        """
        Step 2 & 3: PROXY the payment via Basis Theory.
        We receive a 'card_token' (e.g. token_123) and swap it for real data securely.
        """
        # Basis Theory Proxy Endpoint
        proxy_url = "https://api.basistheory.com/proxy"
        
        # The Target URL (Safepay)
        safepay_target = f"{self.base_url}/order/payments/v3/{tracker}"
        
        headers = {
            "BT-API-KEY": self.bt_private_key,  # Authenticate with Basis Theory
            "BT-PROXY-URL": safepay_target,     # Tell BT where to send the request
            "Content-Type": "application/json",
            "X-SFPY-MERCHANT-SECRET": self.secret_key # Header for Safepay
        }

        # --- STEP A: ATTACH CARD ---
        # We use {{ token.data.field }} syntax. BT replaces this before sending to Safepay.
        attach_payload = {
            "payment_method": {
                "card": {
                    "card_number": f"{{{{ {card_token}.data.number }}}}",
                    "expiration_month": f"{{{{ {card_token}.data.expiration_month }}}}",
                    "expiration_year": f"{{{{ {card_token}.data.expiration_year }}}}",
                    "cvv": f"{{{{ {card_token}.data.cvv }}}}"
                }
            }
        }
        
        print(f"DEBUG: Proxying Card Attachment for tracker {tracker}...")
        resp_attach = requests.post(proxy_url, json=attach_payload, headers=headers)
        
        if resp_attach.status_code not in [200, 201]:
             raise Exception(f"Proxy Attachment Failed: {resp_attach.text}")

        # --- STEP B: AUTHORIZE & CAPTURE ---
        capture_payload = {
            "billing": {
                "street_1": billing_details.get('address', 'St 1'),
                "city": billing_details.get('city', 'Islamabad'),
                "postal_code": billing_details.get('zip', '44000'),
                "country": "PK"
            },
            "authorization": {
                "do_capture": True
            },
            "authentication_setup": {
                "success_url": "http://localhost/success",
                "failure_url": "http://localhost/failure"
            }
        }

        print(f"DEBUG: Proxying Capture for {tracker}...")
        resp_capture = requests.post(proxy_url, json=capture_payload, headers=headers)

        if resp_capture.status_code not in [200, 201]:
             raise Exception(f"Proxy Capture Failed: {resp_capture.text}")
             
        return resp_capture.json()

    def verify_webhook(self, data, signature):
        # (Keep existing webhook logic)
        from safepay_python.safepay import Safepay
        env = Safepay({
            "environment": current_app.config.get('SAFEPAY_ENVIRONMENT', 'sandbox'),
            "apiKey": self.api_key,
            "v1Secret": self.secret_key,
            "webhookSecret": self.webhook_secret,
        })
        return env.is_webhook_valid({"x-sfpy-signature": signature}, {"data": data})