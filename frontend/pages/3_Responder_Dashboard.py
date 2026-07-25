import streamlit as st
import httpx
import os
import time
from datetime import datetime, timezone

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Responder Dashboard", page_icon="🚑", layout="wide")

# ─── Auth Guard ────────────────────────────────────────────────────────────────
if not st.session_state.get("access_token"):
    st.warning("🔒 Please login from the Home page to access this module.")
    st.stop()

AUTH_HEADERS = {"Authorization": f"Bearer {st.session_state.access_token}"}

# ─── Page Header ───────────────────────────────────────────────────────────────
st.title("🚑 Responder Dashboard")
st.markdown("Real-time emergency alerts from users in crisis. This page auto-refreshes every 10 seconds.")
st.markdown("---")

# ─── Fetch Emergencies ─────────────────────────────────────────────────────────
def fetch_emergencies():
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/crisis/emergencies",
            headers=AUTH_HEADERS,
            timeout=10.0
        )
        if response.status_code == 200:
            return response.json().get("emergencies", [])
        return []
    except Exception:
        return None

def resolve_emergency(emergency_id: str) -> bool:
    try:
        response = httpx.patch(
            f"{BACKEND_URL}/api/crisis/emergencies/{emergency_id}/resolve",
            headers=AUTH_HEADERS,
            timeout=10.0
        )
        return response.status_code == 200
    except Exception:
        return False

# ─── Display Alerts ────────────────────────────────────────────────────────────
emergencies = fetch_emergencies()

if emergencies is None:
    st.error("⚠️ Could not connect to the backend. Is it running?")
elif len(emergencies) == 0:
    st.success("✅ No active emergencies. All clear.")
else:
    st.error(f"🆘 **{len(emergencies)} Active Emergency Alert(s)**")
    st.markdown("")

    for alert in emergencies:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 5, 2])

            with col1:
                st.markdown(f"### 👤 {alert.get('user_name', 'Unknown')}")
                st.caption(f"User ID: `{alert.get('user_id', '')[:8]}...`")

            with col2:
                st.markdown("**Last message from user:**")
                st.info(f"_{alert.get('last_message', 'No message recorded.')}_")
                # Format timestamp
                try:
                    ts = alert.get("created_at", "")
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    elapsed = datetime.now(timezone.utc) - dt
                    minutes = int(elapsed.total_seconds() // 60)
                    time_label = f"{minutes} min ago" if minutes > 0 else "Just now"
                    st.caption(f"🕐 Alert triggered: {time_label}")
                except Exception:
                    st.caption(f"🕐 {alert.get('created_at', '')}")

            with col3:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button(
                    "✅ Mark Resolved",
                    key=f"resolve_{alert['id']}",
                    use_container_width=True,
                    type="primary"
                ):
                    if resolve_emergency(alert["id"]):
                        st.success("Marked as resolved!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to resolve.")

# ─── Auto-refresh ──────────────────────────────────────────────────────────────
st.markdown("---")
refresh_col, _ = st.columns([2, 5])
with refresh_col:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()

st.caption("Auto-refreshing every 10 seconds...")
time.sleep(10)
st.rerun()
