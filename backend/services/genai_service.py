import os
import google.generativeai as genai
from pydantic import BaseModel
from typing import Optional
import json

# Setup API Key for Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "DUMMY_KEY_FOR_LOCAL_TESTING"))
model = genai.GenerativeModel('gemini-1.5-flash')

class CrisisRequest(BaseModel):
    user_id: str
    substance: Optional[str] = "unknown"
    situation: str

def generate_crisis_script(request: CrisisRequest):
    """
    Generates a personalized, step-by-step emergency script.
    """
    prompt = f"""
    You are an AI recovery assistant. A user in crisis needs immediate help.
    User Substance: {request.substance}
    Situation: {request.situation}
    
    Provide a calm, grounding, step-by-step de-escalation script.
    Keep it short, direct, and actionable. Do not provide medical advice.
    """
    
    # We use streaming in production, but here we can just return the text
    # or return an iterator for streaming response
    response = model.generate_content(prompt, stream=True)
    return response

def classify_sentiment(text: str):
    """
    Classify user sentiment and craving intensity.
    """
    prompt = f"""
    Analyze the following text from a user in substance recovery.
    Text: "{text}"
    
    Output a JSON object with:
    - sentiment (positive, neutral, negative, crisis)
    - craving_intensity (1-10)
    - recommended_action (e.g. "show grounding exercise", "log positive day")
    """
    
    response = model.generate_content(prompt)
    return response.text

def analyze_self_harm_risk(text: str) -> dict:
    """
    Evaluates if the user is in danger of harming themselves.
    Returns a dict with 'needs_escalation' (bool) and 'reason' (str).
    """
    prompt = f"""
    Analyze the following text from a user in distress for self-harm risk.
    Text: "{text}"
    
    Output ONLY a valid JSON object with:
    - needs_escalation (boolean): true if there is any indication of self-harm, suicide, or severe danger.
    - reason (string): Brief explanation.
    """
    try:
        response = model.generate_content(prompt)
        # Strip potential markdown code blocks
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except Exception as e:
        return {"needs_escalation": False, "reason": "Error parsing risk."}

