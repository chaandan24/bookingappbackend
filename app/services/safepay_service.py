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

        # Ideally, move this to config/env variables as well
        self.bt_private_key = "key_test_us_pvt_UPusvV9PGBX2VXFoegKHDJ.2189b6d4195a4ea5324eced723008158"

    def create_payment_tracker(self, amount, currency="PKR"):
        """
        Step 1: Create the Tracker using v3 Endpoint.
        Returns just the tracker token.
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
            "entry_mode": "flex"
        }
        
        print(f"DEBUG: Creating v3 Tracker at {url}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            json_data = response.json()
            data = json_data.get('data', {})
            
            tracker = None

            # Robust Parsing Logic
            if isinstance(data, dict) and 'tracker' in data:
                tracker_obj = data['tracker']
                if isinstance(tracker_obj, dict) and 'token' in tracker_obj:
                    tracker = tracker_obj['token']
            elif isinstance(data, dict) and 'token' in data:
                tracker = data['token']
            elif isinstance(data, str):
                tracker = data

            if not tracker:
                raise Exception(f"Safepay Init Error: Could not find 'token' in response: {json_data}")

            # Return ONLY the tracker here
            return {"tracker": tracker}
            
        raise Exception(f"Safepay v3 Init Error {response.status_code}: {response.text}")

    def attach_payment_source(self, tracker, card_token):
        """
        Step 2: Attach the Basis Theory Token to the Safepay Tracker.
        This triggers the 3DS Setup and returns the URL + JWT for the Flutter WebView.
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

        # The payload to attach the card
        attach_payload = {
            "payload": {
                "payment_method": {
                    "card": {
                        "card_number": f"{{{{ token: {clean_token} | json: '$.data.number' }}}}",
                        "expiration_month": f"{{{{ token: {clean_token} | json: '$.data.expiration_month' | pad_left: 2, '0' }}}}",
                        "expiration_year": f"{{{{ token: {clean_token} | json: '$.data.expiration_year' | to_string }}}}",
                        "cvv": f"{{{{ token: {clean_token} | json: '$.data.cvc' }}}}"
                    }
                }
            }
        }
    
        print(f"DEBUG: Proxying Card Attachment via Basis Theory...")
        resp_attach = requests.post(proxy_url, json=attach_payload, headers=headers)
    
        if resp_attach.status_code in [200, 201]:
            data = resp_attach.json().get('data', {})
            
            # Extract 3DS Setup Data
            pas_reply = data.get('payment_method', {}).get('payer_authentication_setup', {})
            
            # These are the exact fields required by Cardinal Commerce
            device_data_collection_url = pas_reply.get('device_data_collection_url')
            access_token = pas_reply.get('access_token') # This is the JWT

            if not device_data_collection_url:
                 # It's possible 3DS wasn't required or setup failed silently
                 print(f"WARNING: No device collection URL found in response: {data}")

            return {
                "success": True,
                "device_data_collection_url": device_data_collection_url,
                "access_token": access_token,
                "response": resp_attach.text
            }
        
        print(f"Attach Error Body: {resp_attach.text}")
        raise Exception(f"Proxy Attach Failed: {resp_attach.text}")

    def process_native_payment(self, tracker, billing_details, device_fingerprint_id):
        """
        Step 3: Finalize the payment (Capture).
        Now we include the session ID we got from the Flutter WebView.
        """
        proxy_url = "https://api.basistheory.com/proxy"
        safepay_target_url = f"{self.base_url}/order/payments/v3/{tracker}"
        
        headers = {
            "BT-API-KEY": self.bt_private_key,
            "BT-PROXY-URL": safepay_target_url,
            "Content-Type": "application/json",
            "X-SFPY-MERCHANT-SECRET": self.secret_key
        }

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
                "failure_url": "http://localhost/failure",
                # The ID captured by the Flutter WebView goes here:
                "device_fingerprint_session_id": device_fingerprint_id
            }
        }

        print(f"DEBUG: Proxying Capture via Basis Theory...")
        resp_capture = requests.post(proxy_url, json=capture_payload, headers=headers)

        if resp_capture.status_code not in [200, 201]:
             print(f"Capture Error Body: {resp_capture.text}")
             raise Exception(f"Proxy Capture Failed: {resp_capture.text}")
             
        return resp_capture.json()

    def verify_webhook(self, data, signature):
        from safepay_python.safepay import Safepay
        env = Safepay({
            "environment": current_app.config.get('SAFEPAY_ENVIRONMENT', 'sandbox'),
            "apiKey": self.api_key,
            "v1Secret": self.secret_key,
            "webhookSecret": self.webhook_secret,
        })
        return env.is_webhook_valid({"x-sfpy-signature": signature}, {"data": data})