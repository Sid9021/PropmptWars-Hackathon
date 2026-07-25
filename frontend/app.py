import streamlit as st
import httpx
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Recover Platform", page_icon="🩹", layout="centered")

# --- Session State Initialization ---
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "role" not in st.session_state:
    st.session_state.role = None

# --- Logged In View ---
if st.session_state.access_token:
    st.title("🩹 Recover Platform")
    st.success(f"✅ Welcome back! Use the sidebar to navigate.")
    st.markdown("### A GenAI-Powered Recovery & Prevention Platform")
    st.markdown("""
    Please select a module from the sidebar:
    - **Crisis Response** (Individual)
    - **Caregiver Overdose-Response**
    """)
    if st.button("Logout"):
        st.session_state.access_token = None
        st.session_state.user_id = None
        st.session_state.role = None
        st.rerun()

# --- Auth View ---
else:
    st.title("🩹 Recover Platform")
    st.markdown("### A GenAI-Powered Recovery & Prevention Platform")
    st.markdown("---")

    tab_login, tab_register = st.tabs(["Login", "Create Account"])

    # --- Login Tab ---
    with tab_login:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True, type="primary"):
            if email and password:
                with st.spinner("Logging in..."):
                    try:
                        response = httpx.post(
                            f"{BACKEND_URL}/api/auth/login",
                            json={"email": email, "password": password},
                            timeout=10.0
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.access_token = data["access_token"]
                            st.session_state.user_id = data["user_id"]
                            st.session_state.role = data["role"]
                            st.rerun()
                        else:
                            st.error(response.json().get("detail", "Login failed."))
                    except Exception:
                        st.error("Could not connect to the backend.")
            else:
                st.warning("Please enter your email and password.")

    # --- Register Tab ---
    with tab_register:
        st.subheader("Create Account")
        reg_name = st.text_input("Full Name", key="reg_name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_role = st.selectbox("I am a...", ["user", "caregiver"], key="reg_role")

        if st.button("Create Account", use_container_width=True, type="primary"):
            if reg_name and reg_email and reg_password:
                with st.spinner("Creating account..."):
                    try:
                        response = httpx.post(
                            f"{BACKEND_URL}/api/auth/register",
                            json={
                                "name": reg_name,
                                "email": reg_email,
                                "password": reg_password,
                                "role": reg_role
                            },
                            timeout=10.0
                        )
                        if response.status_code == 201:
                            st.success("Account created! Please login.")
                        else:
                            st.error(response.json().get("detail", "Registration failed."))
                    except Exception:
                        st.error("Could not connect to the backend.")
            else:
                st.warning("Please fill in all required fields.")
