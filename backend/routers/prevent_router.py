from fastapi import APIRouter
from pydantic import BaseModel

from ..services.genai_service import classify_sentiment

router = APIRouter(prefix="/api/prevent", tags=["prevent"])

class CheckinRequest(BaseModel):
    user_id: str
    text_input: str

@router.post("/checkin")
async def checkin_endpoint(request: CheckinRequest):
    """
    Adaptive daily check-in.
    """
    result = classify_sentiment(request.text_input)
    return {"analysis": result}

@router.get("/education")
async def get_education(user_id: str):
    """
    Fetch personalized micro-education.
    """
    # Placeholder for fetching based on risk profile
    return {"content": "Here is some micro-education based on your profile."}
