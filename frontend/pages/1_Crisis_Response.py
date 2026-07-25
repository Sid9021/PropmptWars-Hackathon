import streamlit as st
import httpx
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Crisis Response", page_icon="🚨", layout="centered")

# --- Auth Guard ---
if not st.session_state.get("access_token"):
    st.warning("🔒 Please login from the Home page to access this module.")
    st.stop()

AUTH_HEADERS = {"Authorization": f"Bearer {st.session_state.access_token}"}

# --- Page UI ---
st.title("🚨 Crisis Response")
st.markdown("### I need help now.")

if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""
if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None

# Audio input widget for voice recording
audio_file = st.audio_input("🎤 Record your voice (SOS/Voice Help)")

if audio_file is not None:
    audio_bytes = audio_file.read()
    if st.session_state.last_audio_bytes != audio_bytes:
        st.session_state.last_audio_bytes = audio_bytes
        with st.spinner("Transcribing your voice..."):
            try:
                files = {"file": ("recording.wav", audio_bytes, "audio/wav")}
                response = httpx.post(
                    f"{BACKEND_URL}/api/crisis/transcribe",
                    files=files,
                    headers=AUTH_HEADERS,
                    timeout=30.0
                )
                if response.status_code == 200:
                    st.session_state.transcribed_text = response.json().get("text", "")
                    st.success("Voice transcribed successfully!")
                else:
                    st.error(f"Failed to transcribe: {response.text}")
            except Exception as e:
                st.error("Failed to connect to backend for transcription.")

situation = st.text_input(
    "What are you experiencing right now?",
    value=st.session_state.transcribed_text,
    placeholder="e.g. I am having a strong craving"
)

if st.button("🆘 Get Help (Tap or Voice)", use_container_width=True, type="primary"):
    if situation:
        with st.spinner("Connecting..."):
            try:
                response = httpx.post(
                    f"{BACKEND_URL}/api/crisis/sos",
                    json={"user_id": st.session_state.user_id, "substance": "unknown", "situation": situation},
                    headers=AUTH_HEADERS,
                    timeout=30.0
                )
                if response.status_code == 200:
                    response_text = response.text
                    st.success("Here is a step-by-step grounding exercise:")
                    st.write(response_text)
                    
                    # Generate speech de-escalation voice output
                    with st.spinner("Generating voice response..."):
                        try:
                            tts_response = httpx.post(
                                f"{BACKEND_URL}/api/crisis/speak",
                                json={"text": response_text},
                                headers=AUTH_HEADERS,
                                timeout=20.0
                            )
                            if tts_response.status_code == 200:
                                st.audio(tts_response.content, format="audio/wav", autoplay=True)
                            else:
                                st.warning("Voice playback generation failed.")
                        except Exception:
                            st.warning("Failed to connect to voice service.")
                elif response.status_code == 401:
                    st.error("Session expired. Please login again.")
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error("Failed to connect to backend.")
    else:
        st.warning("Please describe your situation or use voice.")

st.markdown("---")
if st.button("📞 Call 988 (Crisis Lifeline)", use_container_width=True):
    st.info("Dialing 988...")
