from pydantic import BaseModel, Field  #type: ignore

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