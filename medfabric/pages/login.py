import streamlit as st
from utils.db.database import get_session
from api.credentials import login_doctor

st.set_page_config(
    page_title="Login",
    page_icon=":key:",
    layout="centered",
)
with st.form("login_form", clear_on_submit=True, enter_to_submit=True, border=True):
    st.title("Login to MedFabric")
    username_input = st.text_input("Username:")
    password_input = st.text_input("Password:", type="password")

    if st.form_submit_button("Login"):
        if not username_input or not password_input:
            st.error("Please enter both username and password.")
        with get_session() as session:
            doctor = login_doctor(session, username_input, password_input)
            if doctor:
                st.success("Login successful")

                # e.g., store in session_state
                st.session_state.user = doctor.uuid
                st.switch_page("pages/dashboard.py")
            else:
                st.error("Invalid username or password")

if st.button("Register"):
    st.switch_page("pages/register.py")
