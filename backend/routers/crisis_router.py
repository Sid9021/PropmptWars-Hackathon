from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from ..services.genai_service import generate_crisis_script, CrisisRequest, analyze_self_harm_risk
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/api/crisis", tags=["crisis"])


class CaregiverRequest(BaseModel):
    is_breathing: bool
    is_responsive: bool
    has_naloxone: bool


@router.post("/sos")
async def sos_endpoint(request: CrisisRequest, current_user: dict = Depends(get_current_user)):
    """
    Handle voice/text input and return personalized streaming scripts.
    Requires a valid JWT Bearer token.
    """
    # Inject authenticated user_id so users can't spoof each other
    request.user_id = current_user["user_id"]
    try:
        response_stream = generate_crisis_script(request)

        async def stream_generator():
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        return StreamingResponse(stream_generator(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/caregiver")
async def caregiver_endpoint(request: CaregiverRequest, current_user: dict = Depends(get_current_user)):
    """
    Caregiver overdose-response workflow.
    Requires a valid JWT Bearer token.
    """
    if not request.is_breathing or not request.is_responsive:
        return {"action": "CALL_911", "script": "The person is not responsive or not breathing. Please call 911 immediately. Administer Naloxone if available."}
    return {"action": "MONITOR", "script": "Keep monitoring the person. Ensure they stay awake and responsive."}


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat_endpoint(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    AI chat endpoint that checks for self-harm risk before responding.
    Requires a valid JWT Bearer token. user_id is taken from the token.
    """
    user_id = current_user["user_id"]

    # 1. Analyze risk
    risk_assessment = analyze_self_harm_risk(request.message)

    if risk_assessment.get("needs_escalation"):
        return {
            "needs_escalation": True,
            "reply": "I am concerned for your safety. I am connecting you to emergency services immediately.",
            "reason": risk_assessment.get("reason")
        }

    # 2. If safe, generate a supportive AI response
    reply_stream = generate_crisis_script(CrisisRequest(
        user_id=user_id,
        situation=f"User says: {request.message}. Respond with emotional support and de-escalation."
    ))

    full_reply = ""
    for chunk in reply_stream:
        if chunk.text:
            full_reply += chunk.text

    return {
        "needs_escalation": False,
        "reply": full_reply
    }
