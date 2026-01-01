"""
XPay Pakistan Payment Service for Flask
https://xpay.postexglobal.com (by XStak)

Native Flutter SDK integration - NO WebView redirect needed!
"""

import hmac
import hashlib
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any


class XPayService:
    """XPay Pakistan payment gateway service"""
    
    # API Endpoints
    STAGING_BASE_URL = "https://xstak-pay-stg.xstak.com"
    PRODUCTION_BASE_URL = "https://xstak-pay.xstak.com"
    
    def __init__(
        self,
        public_key: str,
        hmac_key: str,
        account_id: str,
        environment: str = "staging"
    ):
        """
        Initialize XPay service.
        
        Get these from XPay Admin Portal (XAP):
        - public_key: Found in Store Settings > Keys
        - hmac_key: API HMAC Key from Keys section
        - account_id: Your XPay account ID
        """
        self.public_key = public_key
        self.hmac_key = hmac_key
        self.account_id = account_id
        self.base_url = (
            self.PRODUCTION_BASE_URL 
            if environment == "production" 
            else self.STAGING_BASE_URL
        )
    
    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """
        Generate HMAC SHA-256 signature for API requests.
        
        The signature is created using the API HMAC Key found in 
        the keys section of XAP dashboard.
        """
        payload_string = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            self.hmac_key.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def create_payment_intent(
        self,
        amount: float,
        currency: str = "PKR",
        order_id: str = None,
        customer_name: str = None,
        customer_email: str = None,
        customer_phone: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent to get clientSecret and encryptionKey.
        
        These are required by the Flutter SDK's confirmPayment() method.
        
        Args:
            amount: Payment amount (in PKR or specified currency)
            currency: Currency code (default: PKR)
            order_id: Your internal order/booking ID
            customer_name: Customer's name
            customer_email: Customer's email
            customer_phone: Customer's phone (with country code)
            metadata: Additional data to store with payment
            
        Returns:
            {
                "success": True,
                "pi_id": "pi_xxx",
                "pi_client_secret": "pi_secret_xxx",
                "encryption_key": "enc_key_xxx"
            }
        """
        endpoint = f"{self.base_url}/public/v1/payment/intent"
        
        # Build payload
        payload = {
            "amount": int(amount * 100),  # Convert to paisa (smallest unit)
            "currency": currency,
            "account_id": self.account_id,
        }
        
        if order_id:
            payload["order_id"] = order_id
        
        if customer_name or customer_email or customer_phone:
            payload["customer"] = {}
            if customer_name:
                payload["customer"]["name"] = customer_name
            if customer_email:
                payload["customer"]["email"] = customer_email
            if customer_phone:
                payload["customer"]["phone"] = customer_phone
        
        if metadata:
            payload["metadata"] = metadata
        
        # Generate signature
        signature = self._generate_signature(payload)
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.public_key,
            "x-signature": signature,
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "pi_id": data.get("pi_id"),
                "pi_client_secret": data.get("pi_client_secret"),
                "encryption_key": data.get("encryption_key"),
                "raw_response": data
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "raw_response": getattr(e.response, 'text', None)
            }
    
    def get_payment_status(self, pi_id: str) -> Dict[str, Any]:
        """
        Get payment intent status.
        
        Args:
            pi_id: Payment intent ID from create_payment_intent
            
        Returns:
            Payment status and details
        """
        endpoint = f"{self.base_url}/public/v1/payment/intent/{pi_id}"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.public_key,
        }
        
        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: str
    ) -> bool:
        """
        Verify webhook signature for payment notifications.
        
        Args:
            payload: Raw request body bytes
            signature: x-signature header from webhook
            webhook_secret: Your webhook secret from XAP
            
        Returns:
            True if signature is valid
        """
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)