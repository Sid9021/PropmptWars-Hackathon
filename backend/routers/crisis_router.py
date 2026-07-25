import uuid
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional, List

from ..services.genai_service import generate_crisis_script, CrisisRequest, analyze_self_harm_risk, transcribe_audio
from ..services.tts_service import generate_speech
from ..services.auth_service import get_current_user
from ..db import get_db

router = APIRouter(prefix="/api/crisis", tags=["crisis"])


# ─── Models ────────────────────────────────────────────────────────────────────

class CaregiverRequest(BaseModel):
    is_breathing: bool
    is_responsive: bool
    has_naloxone: bool


class ChatRequest(BaseModel):
    message: str


class SpeakRequest(BaseModel):
    text: str


class EmergencyRequest(BaseModel):
    last_message: Optional[str] = "User triggered emergency."


# ─── SOS ───────────────────────────────────────────────────────────────────────

@router.post("/sos")
async def sos_endpoint(request: CrisisRequest, current_user: dict = Depends(get_current_user)):
    """
    Handle voice/text input and return personalized streaming scripts.
    Requires a valid JWT Bearer token.
    """
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


# ─── Caregiver ─────────────────────────────────────────────────────────────────

@router.post("/caregiver")
async def caregiver_endpoint(request: CaregiverRequest, current_user: dict = Depends(get_current_user)):
    """
    Caregiver overdose-response workflow.
    Requires a valid JWT Bearer token.
    """
    if not request.is_breathing or not request.is_responsive:
        return {
            "action": "CALL_911",
            "script": "The person is not responsive or not breathing. Please call 911 immediately. Administer Naloxone if available."
        }
    return {"action": "MONITOR", "script": "Keep monitoring the person. Ensure they stay awake and responsive."}


# ─── Chat ──────────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    AI chat endpoint that checks for self-harm risk before responding.
    Requires a valid JWT Bearer token.
    """
    user_id = current_user["user_id"]

    # 1. Analyze risk
    risk_assessment = analyze_self_harm_risk(request.message)

    if risk_assessment.get("needs_escalation"):
        return {
            "needs_escalation": True,
            "reply": "I am concerned for your safety. Please reach out to emergency services or a trusted person immediately.",
            "reason": risk_assessment.get("reason")
        }

    # 2. Generate supportive AI response
    reply_stream = generate_crisis_script(CrisisRequest(
        user_id=user_id,
        situation=f"User says: {request.message}. Respond with emotional support and de-escalation."
    ))

    full_reply = ""
    for chunk in reply_stream:
        if chunk.text:
            full_reply += chunk.text

    return {"needs_escalation": False, "reply": full_reply}


# ─── TTS / Speak ───────────────────────────────────────────────────────────────

@router.post("/speak")
async def speak_endpoint(request: SpeakRequest, current_user: dict = Depends(get_current_user)):
    """
    Convert text to speech using Gemini TTS.
    Returns a WAV audio file.
    Requires a valid JWT Bearer token.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    try:
        audio_bytes = generate_speech(request.text.strip())
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={"Content-Disposition": "inline; filename=response.wav"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


# ─── Emergency Alert ──────────────────────────────────────────────────────────

@router.post("/emergency")
async def trigger_emergency(request: EmergencyRequest, current_user: dict = Depends(get_current_user)):
    """
    Mobile user triggers an emergency alert.
    This logs the alert to the DB so the Responder Dashboard can display it.
    """
    user_id = current_user["user_id"]
    emergency_id = str(uuid.uuid4())

    with get_db() as conn:
        # Look up user's name from the users table
        user_row = conn.execute(
            "SELECT name FROM users WHERE id = ?", [user_id]
        ).fetchone()
        user_name = user_row[0] if user_row else "Unknown User"

        conn.execute(
            """
            INSERT INTO emergencies (id, user_id, user_name, last_message, is_resolved)
            VALUES (?, ?, ?, ?, FALSE)
            """,
            [emergency_id, user_id, user_name, request.last_message]
        )

    return {
        "emergency_id": emergency_id,
        "message": "Emergency alert sent. A responder has been notified. Help is on the way."
    }


@router.get("/emergencies")
async def list_emergencies(current_user: dict = Depends(get_current_user)):
    """
    Returns all unresolved emergency alerts. 
    Intended for the Streamlit Responder Dashboard.
    """
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, user_name, last_message, is_resolved, created_at
            FROM emergencies
            WHERE is_resolved = FALSE
            ORDER BY created_at DESC
            """
        ).fetchall()

    return {
        "emergencies": [
            {
                "id": row[0],
                "user_id": row[1],
                "user_name": row[2],
                "last_message": row[3],
                "is_resolved": row[4],
                "created_at": str(row[5]),
            }
            for row in rows
        ]
    }


@router.patch("/emergencies/{emergency_id}/resolve")
async def resolve_emergency(emergency_id: str, current_user: dict = Depends(get_current_user)):
    """
    Mark an emergency alert as resolved. Called from the Responder Dashboard.
    """
    with get_db() as conn:
        result = conn.execute(
            "SELECT id FROM emergencies WHERE id = ?", [emergency_id]
        ).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Emergency not found.")

        conn.execute(
            "UPDATE emergencies SET is_resolved = TRUE WHERE id = ?",
            [emergency_id]
        )

    return {"message": "Emergency marked as resolved."}


@router.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Transcribe uploaded audio file using Gemini.
    """
    audio_bytes = await file.read()
    mime_type = file.content_type or "audio/wav"
    try:
        text = transcribe_audio(audio_bytes, mime_type)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

