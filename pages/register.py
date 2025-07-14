import time
import streamlit as st
from db import get_session
from credentials import register_doctor

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
                doctor = register_doctor(session, username_input, password_input_1)
                if doctor:
                    st.success("Registration successful")
                    time.sleep(1)
                    st.switch_page("login.py")
