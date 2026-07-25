import streamlit as st
import httpx
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Caregiver Response", page_icon="❤️", layout="centered")

# --- Auth Guard ---
if not st.session_state.get("access_token"):
    st.warning("🔒 Please login from the Home page to access this module.")
    st.stop()

AUTH_HEADERS = {"Authorization": f"Bearer {st.session_state.access_token}"}

# --- Page UI ---
st.title("❤️ Caregiver Emergency")
st.markdown("### Answer quickly to get help:")

is_breathing = st.radio("Is the person breathing?", ("Yes", "No", "Not Sure"))
is_responsive = st.radio("Are they responsive?", ("Yes", "No"))
has_naloxone = st.radio("Do you have Naloxone on hand?", ("Yes", "No"))

if st.button("Generate Response Script", use_container_width=True, type="primary"):
    with st.spinner("Analyzing..."):
        try:
            req_data = {
                "is_breathing": is_breathing == "Yes",
                "is_responsive": is_responsive == "Yes",
                "has_naloxone": has_naloxone == "Yes"
            }
            response = httpx.post(
                f"{BACKEND_URL}/api/crisis/caregiver",
                json=req_data,
                headers=AUTH_HEADERS,
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                st.write(f"**Action:** {data.get('action')}")
                st.write(data.get("script"))
            elif response.status_code == 401:
                st.error("Session expired. Please login again.")
            else:
                st.error("Error connecting to backend.")
        except Exception:
            st.error("Backend not reachable.")

st.markdown("---")
if st.button("📞 Call 911", use_container_width=True):
    st.error("Dialing 911...")
