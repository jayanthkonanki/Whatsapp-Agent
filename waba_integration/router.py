from fastapi import APIRouter, Depends, HTTPException, Query
from .schemas import PhoneRegistrationRequest
from .manager import WABAManager
import os

router = APIRouter(prefix="/waba", tags=["WhatsApp Business v24.0 Testing"])

# In a test environment, these can be hardcoded or set in .env
def get_waba_manager():
    APP_ID = "1650815602581824"  # From your provided image
    APP_SECRET = os.getenv("META_APP_SECRET", "") 
    return WABAManager(APP_ID, APP_SECRET)

@router.post("/test-register", summary="Directly Register Phone via App Token")
async def test_register_phone(
    request: PhoneRegistrationRequest,
    # Allow passing the app token directly in the query for easy Swagger testing
    token: str = Query(..., description="Paste your App Token here"),
    manager: WABAManager = Depends(get_waba_manager)
):
    """
    Use this to test the integration. 
    1. Enter the Phone Number ID from your Meta Dashboard.
    2. Enter a 6-digit PIN.
    3. Provide the App Token from your screenshot.
    """
    success = await manager.register_phone(request.phone_number_id, token, request.pin)
    
    if success:
        manager.store_credentials(request.user_id, token, request.phone_number_id)
        return {"status": "success", "message": f"Number {request.phone_number_id} is now LIVE."}
    
    raise HTTPException(status_code=400, detail="Registration failed.")