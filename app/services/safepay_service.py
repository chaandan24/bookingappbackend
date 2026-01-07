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

        self.bt_private_key = "key_test_us_pvt_UPusvV9PGBX2VXFoegKHDJ.2189b6d4195a4ea5324eced723008158"

    def create_payment_tracker(self, amount, currency="PKR"):
        """
        Step 1: Create the Tracker using v3 Endpoint.
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
        
        print(f"DEBUG: Creating v3 Tracker at {url}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            json_data = response.json()
            data = json_data.get('data', {})
            
            # 👇 ROBUST PARSING LOGIC
            tracker = None

            # Case A: Nested v3 structure (data -> tracker -> token)
            # This matches the error log you just shared.
            if isinstance(data, dict) and 'tracker' in data:
                tracker_obj = data['tracker']
                if isinstance(tracker_obj, dict) and 'token' in tracker_obj:
                    tracker = tracker_obj['token']

            # Case B: Flat structure (data -> token)
            elif isinstance(data, dict) and 'token' in data:
                tracker = data['token']
            
            # Case C: Direct string (data is the token)
            elif isinstance(data, str):
                tracker = data
            
            # Validation
            if not tracker:
                print(f"DEBUG: Parsed Data: {data}")
                raise Exception(f"Safepay Init Error: Could not find 'token' in response: {json_data}")

            return {"tracker": tracker}
            
        raise Exception(f"Safepay v3 Init Error {response.status_code}: {response.text}")

    def process_native_payment(self, tracker, card_token, billing_details):
        """
        Step 2: Proxy the payment via Basis Theory.
        We receive a 'card_token' (e.g. token_123) and swap it for real data securely.
        """

        clean_token = card_token.strip()
        
    
        proxy_url = "https://api.basistheory.com/proxy"
        
        safepay_target_url = f"{self.base_url}/order/payments/v3/{tracker}"
        
        headers = {
            "BT-API-KEY": self.bt_private_key,
            "BT-PROXY-URL": safepay_target_url,
            "Content-Type": "application/json",
            "X-SFPY-MERCHANT-SECRET": self.secret_key
        }
        attach_payload = {
            "payload" : {
                "payment_method": {
                    "card": {
                        "card_number": f"{{{{ token: {clean_token} | json: '$.data.number' }}}}",
                        "expiration_month": f"{{{{ token: {clean_token} | json: '$.data.expiration_month' | pad_left: 2, '0' }}}}",
                        "expiration_year": f"{{{{ token: {clean_token} | json: '$.data.expiration_year | to_string | slice: -2, 2' }}}}",
                        "cvv": f"{{{{ token: {clean_token} | json: '$.data.cvc' }}}}"
                    }
                }
            }
        }
        
        print(f"DEBUG: Proxying Card Attachment via Basis Theory...")
        resp_attach = requests.post(proxy_url, json=attach_payload, headers=headers)
        
        # Check for Proxy Errors
        if resp_attach.status_code not in [200, 201]:
             print(f"Proxy Error Body: {resp_attach.text}")
             raise Exception(f"Proxy Attachment Failed: {resp_attach.text}")

        # --- REQUEST 2: AUTHORIZE & CAPTURE ---
        # We can send this directly to Safepay (since no card data), 
        # BUT using the proxy again is safer to keep headers/IP consistent.
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

        print(f"DEBUG: Proxying Capture via Basis Theory...")
        resp_capture = requests.post(proxy_url, json=capture_payload, headers=headers)

        if resp_capture.status_code not in [200, 201]:
             print(f"Capture Error Body: {resp_capture.text}")
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