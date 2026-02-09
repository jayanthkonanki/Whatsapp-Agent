from fastapi import APIRouter, Depends, HTTPException  #type: ignore
from .schemas import TokenExchangeRequest, PhoneRegistrationRequest
from .manager import WABAManager
import os

router = APIRouter(prefix="/waba", tags=["WhatsApp Business API"])

# dependency to get the manager instance (Singleton pattern recommended)
def get_waba_manager():
    # In a real app, load these from environment variables
    APP_ID = os.getenv("META_APP_ID", "your_app_id")
    APP_SECRET = os.getenv("META_APP_SECRET", "your_app_secret")
    return WABAManager(APP_ID, APP_SECRET)

@router.post("/auth/exchange")
async def exchange_token(
    request: TokenExchangeRequest, 
    manager: WABAManager = Depends(get_waba_manager)
):
    """
    Step 1: Exchange temporary code for a permanent access token.
    This token allows you to manage the user's WABA.
    """
    token = await manager.exchange_code_for_token(request.temp_code)
    
    # Store the token temporarily or partially; usually, we wait for full WABA details
    # For this flow, we might return it to the frontend or cache it
    return {"status": "success", "access_token": token, "message": "Token exchanged successfully"}

@router.post("/onboard/register")
async def register_phone(
    request: PhoneRegistrationRequest,
    access_token: str, # Passed via header or body in real flow
    waba_id: str,      # Usually obtained from the frontend flow or a previous step
    manager: WABAManager = Depends(get_waba_manager)
):
    """
    Step 2: Register the phone number with a PIN.
    This enables the 'Pipe' for this specific agent.
    """
    success = await manager.register_phone(request.phone_number_id, access_token, request.pin)
    
    if success:
        # Step 3: Secure Storage
        manager.store_credentials(
            user_id=request.user_id,
            access_token=access_token,
            waba_id=waba_id,
            phone_number_id=request.phone_number_id
        )
        return {"status": "registered", "message": "Phone number registered and pipeline ready."}
    
    raise HTTPException(status_code=400, detail="Registration failed")