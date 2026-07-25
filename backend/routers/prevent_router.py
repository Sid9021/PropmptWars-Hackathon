from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..services.genai_service import classify_sentiment
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/api/prevent", tags=["prevent"])


class CheckinRequest(BaseModel):
    text_input: str


@router.post("/checkin")
async def checkin_endpoint(request: CheckinRequest, current_user: dict = Depends(get_current_user)):
    """
    Adaptive daily check-in.
    Requires a valid JWT Bearer token.
    """
    result = classify_sentiment(request.text_input)
    return {"user_id": current_user["user_id"], "analysis": result}


@router.get("/education")
async def get_education(current_user: dict = Depends(get_current_user)):
    """
    Fetch personalized micro-education.
    Requires a valid JWT Bearer token.
    """
    return {
        "user_id": current_user["user_id"],
        "content": "Here is some micro-education based on your profile."
    }
