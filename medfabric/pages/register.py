import time
import streamlit as st
from medfabric.db.database import get_session
from medfabric.api.credentials import register_doctor, check_doctor_already_exists

st.set_page_config(
    page_title="Register",
    page_icon=":memo:",
    layout="centered",
)
with st.form(
    "registration_form", clear_on_submit=True, enter_to_submit=True, border=True
):
    st.title("Register for MedFabric")
    username_input = st.text_input("Username:")
    password_input_1 = st.text_input("Password:", type="password")
    password_input_2 = st.text_input("Confirm Password:", type="password")

    if st.form_submit_button("Register"):
        if not username_input or not password_input_1 or not password_input_2:
            st.error("Please fill out all fields.")
        elif password_input_1 != password_input_2:
            st.error("Passwords do not match.")
        else:
            with get_session() as session:
                if check_doctor_already_exists(session, username_input):
                    st.error("Username already exists. Please choose another.")
                elif len(password_input_1) < 8:
                    st.error("Password must be at least 8 characters long.")
                else:
                    doctor = register_doctor(session, username_input, password_input_1)
                    if doctor:
                        st.success("Registration successful")
                        time.sleep(1)
                        st.switch_page("pages/login.py")
