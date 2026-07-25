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

situation = st.text_input(
    "What are you experiencing right now?",
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
                    st.success("Here is a step-by-step grounding exercise:")
                    st.write(response.text)
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
