import httpx #type: ignore
import logging
from typing import Dict, Optional
from fastapi import HTTPException  #type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WABAManager:
    def __init__(self, app_id: str, app_secret: str, api_version: str = "v19.0"):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = f"https://graph.facebook.com/{api_version}"
        
        # Simple in-memory storage for demonstration. 
        # In production, replace this with a database (PostgreSQL/MongoDB).
        self._credential_store: Dict[str, Dict] = {}

    async def exchange_code_for_token(self, code: str) -> str:
        """
        Exchanges a temporary auth code for a long-lived user access token.
        """
        params = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "code": code,
            "grant_type": "authorization_code"
            # Note: redirect_uri might be required depending on your Meta App setup
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/oauth/access_token", params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("access_token")
            except httpx.HTTPStatusError as e:
                logger.error(f"Token exchange failed: {e.response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to exchange token: {e.response.text}")

    async def register_phone(self, phone_number_id: str, access_token: str, pin: str) -> bool:
        """
        Registers the phone number with a 6-digit PIN to enable messaging.
        """
        url = f"{self.base_url}/{phone_number_id}/register"
        payload = {
            "messaging_product": "whatsapp",
            "pin": pin
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                
                # Check for specific error codes or success
                if response.status_code == 200:
                    return True
                
                error_data = response.json()
                logger.error(f"Registration failed: {error_data}")
                raise HTTPException(status_code=response.status_code, detail=error_data)
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error during registration: {e.response.text}")
                raise HTTPException(status_code=500, detail="Phone registration failed.")

    def store_credentials(self, user_id: str, access_token: str, waba_id: str, phone_number_id: str):
        """
        Securely stores the credentials associated with a user.
        """
        self._credential_store[user_id] = {
            "access_token": access_token,
            "waba_id": waba_id,
            "phone_number_id": phone_number_id
        }
        logger.info(f"Credentials stored for user {user_id}")

    def get_credentials(self, user_id: str) -> Optional[Dict]:
        return self._credential_store.get(user_id)