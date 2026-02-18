import httpx
import logging
from typing import Dict, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class WABAManager:
    def __init__(self, app_id: str, app_secret: str, api_version: str = "v24.0"):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = f"https://graph.facebook.com/{api_version}"
        self._credential_store: Dict[str, Dict] = {}

    async def register_phone(self, phone_number_id: str, access_token: str, pin: str) -> bool:
        """
        v24.0 Registration: Pairs the phone number ID with your WABA.
        Required for Cloud API to send messages.
        """
        url = f"{self.base_url}/{phone_number_id}/register"
        payload = {
            "messaging_product": "whatsapp",
            "pin": pin  # 6-digit registration PIN
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return True
            
            error_details = response.json()
            logger.error(f"v24.0 Registration Failed: {error_details}")
            raise HTTPException(status_code=response.status_code, detail=error_details)

    def store_credentials(self, user_id: str, access_token: str, phone_number_id: str):
        self._credential_store[user_id] = {
            "access_token": access_token,
            "phone_number_id": phone_number_id
        }