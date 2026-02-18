from pydantic import BaseModel, Field  #type: ignore
from typing import Optional, Dict, Any

class TokenExchangeRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user in your system")
    temp_code: str = Field(..., description="Temporary code from Meta Embedded Signup")

class PhoneRegistrationRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    phone_number_id: str = Field(..., description="The specific phone ID to register")
    pin: str = Field(..., min_length=6, max_length=6, description="6-digit PIN for 2FA registration")

class WABACredentials(BaseModel):
    access_token: str
    waba_id: str
    phone_number_id: str

# --- NEW SCHEMAS FOR TESTING ---

class SendMessageRequest(BaseModel):
    """Used to manually trigger a message via Swagger UI"""
    to_phone: str = Field(..., description="Recipient phone number (e.g. 919876543210)")
    message_body: str = Field(..., description="Text content to send")
    # Optional: Allow overriding env vars for quick testing
    custom_access_token: Optional[str] = None
    custom_phone_id: Optional[str] = None

class WebhookPayload(BaseModel):
    """Simplified schema to validate incoming webhook data"""
    object: str
    entry: list