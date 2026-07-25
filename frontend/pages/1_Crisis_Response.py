import streamlit as st
import httpx
import json

st.set_page_config(page_title="Crisis Response", page_icon="🚨", layout="centered")

st.title("🚨 Crisis Response")

st.markdown("### I need help now.")

# Placeholder for real voice integration, we use text for prototype MVP if streamlit-webrtc isn't fully set up for stt yet
situation = st.text_input("What are you experiencing right now?", placeholder="e.g. I am having a strong craving")

if st.button("🆘 Get Help (Tap or Voice)", use_container_width=True, type="primary"):
    if situation:
        with st.spinner("Connecting..."):
            try:
                # In a real app this would stream
                response = httpx.post(
                    "http://localhost:8000/api/crisis/sos",
                    json={"user_id": "user123", "substance": "unknown", "situation": situation},
                    timeout=10.0
                )
                if response.status_code == 200:
                    st.success("Here is a step-by-step grounding exercise:")
                    st.write(response.text)
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error("Failed to connect to backend.")
    else:
        st.warning("Please describe your situation or use voice.")

st.markdown("---")
if st.button("📞 Call 988 (Crisis Lifeline)", use_container_width=True):
    st.info("Dialing 988...")
