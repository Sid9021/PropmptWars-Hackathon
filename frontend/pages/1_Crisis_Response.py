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

import streamlit.components.v1 as components

# --- Check for voice input cache on Rerun ---
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""

try:
    voice_resp = httpx.get(
        f"{BACKEND_URL}/api/crisis/voice-input",
        headers=AUTH_HEADERS,
        timeout=5.0
    )
    if voice_resp.status_code == 200:
        new_text = voice_resp.json().get("text")
        if new_text:
            st.session_state.transcribed_text = new_text
except Exception:
    pass

st.markdown("### 🎙️ Voice Input (Push-To-Talk)")
st.caption("Press and hold the button below to speak, then release it to send your message.")

# Embed premium styled custom Push-To-Talk component
ptt_html = """
<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: sans-serif; gap: 8px; margin: 10px 0;">
    <button id="record-btn" style="
        background: linear-gradient(135deg, #1f6feb, #0969da);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 14px 28px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(31, 111, 235, 0.4);
        transition: all 0.2s ease;
        user-select: none;
        -webkit-user-select: none;
        outline: none;
        width: 100%;
        max-width: 320px;
        text-align: center;
    ">🎙️ Hold to Speak</button>
    <div id="status" style="color: #888; font-size: 14px;">Let go to transcribe</div>
</div>

<script>
    const recordBtn = document.getElementById('record-btn');
    const statusDiv = document.getElementById('status');
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;

    const backendUrl = "BACKEND_URL_PLACEHOLDER";
    const token = "TOKEN_PLACEHOLDER";

    async function startRecording() {
        audioChunks = [];
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                statusDiv.innerText = "Transcribing your voice...";
                
                const formData = new FormData();
                formData.append('file', audioBlob, 'recording.wav');

                try {
                    const response = await fetch(`${backendUrl}/api/crisis/voice-input`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        },
                        body: formData
                    });
                    if (response.ok) {
                        statusDiv.innerText = "Done!";
                        // Notify Streamlit and reload parent page
                        window.parent.postMessage({type: 'streamlit:setComponentValue', value: Date.now()}, '*');
                        setTimeout(() => {
                            window.parent.location.reload();
                        }, 400);
                    } else {
                        statusDiv.innerText = "Transcription failed.";
                    }
                } catch (err) {
                    statusDiv.innerText = "Network error.";
                }
            };
            mediaRecorder.start();
            isRecording = true;
            recordBtn.style.background = 'linear-gradient(135deg, #ea4a5a, #d73a49)';
            recordBtn.style.transform = 'scale(0.97)';
            recordBtn.innerText = "🔴 Listening... let go";
            statusDiv.innerText = "Recording...";
        } catch (err) {
            statusDiv.innerText = "Mic access denied or unsupported.";
        }
    }

    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            isRecording = false;
            recordBtn.style.background = 'linear-gradient(135deg, #1f6feb, #0969da)';
            recordBtn.style.transform = 'scale(1)';
            recordBtn.innerText = "🎙️ Hold to Speak";
        }
    }

    recordBtn.addEventListener('mousedown', startRecording);
    recordBtn.addEventListener('mouseup', stopRecording);
    recordBtn.addEventListener('mouseleave', stopRecording);

    recordBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        startRecording();
    });
    recordBtn.addEventListener('touchend', (e) => {
        e.preventDefault();
        stopRecording();
    });
</script>
"""

# Format placeholders manually to avoid Python f-string curly-brace interpolation errors
ptt_html = ptt_html.replace("BACKEND_URL_PLACEHOLDER", BACKEND_URL).replace("TOKEN_PLACEHOLDER", st.session_state.access_token)

# Render custom component
components.html(ptt_html, height=95)

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
