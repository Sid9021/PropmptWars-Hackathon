import os
import wave
from google import genai
from google.genai import types

# Use the new google-genai client for TTS
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", "DUMMY_KEY"))

# A calm, steady voice suitable for crisis de-escalation
VOICE_NAME = "Kore"
TTS_MODEL = "gemini-2.5-flash-preview-tts"

# System prompt to guide tone
TTS_SYSTEM_PROMPT = (
    "Speak in a calm, warm, and reassuring tone. "
    "You are helping someone through a difficult moment. "
    "Speak slowly and clearly."
)


def generate_speech(text: str) -> bytes:
    """
    Generate speech audio from text using Gemini TTS.
    Returns raw WAV audio bytes.
    Raises on failure — callers should handle gracefully.
    """
    response = _client.models.generate_content(
        model=TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=TTS_SYSTEM_PROMPT,
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=VOICE_NAME
                    )
                )
            ),
        ),
    )

    # Extract raw PCM audio bytes from the response
    audio_data = response.candidates[0].content.parts[0].inline_data.data

    # Wrap the raw PCM bytes in a proper WAV container so browsers/apps can play it
    wav_bytes = _pcm_to_wav(audio_data, sample_rate=24000, channels=1, sample_width=2)
    return wav_bytes


def _pcm_to_wav(pcm_data: bytes, sample_rate: int, channels: int, sample_width: int) -> bytes:
    """Wrap raw PCM audio data in a WAV file header."""
    import io
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return buffer.getvalue()
