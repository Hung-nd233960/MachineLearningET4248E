import time
import streamlit as st
from medfabric.api.credentials import register_doctor, check_doctor_already_exists
from medfabric.api.errors import (
    DatabaseError,
    DuplicateEntryError,
)

st.set_page_config(
    page_title="Register",
    page_icon=":memo:",
    layout="centered",
)
session = st.session_state.get("db_session")
if session is None:
    st.error("Database session not found. Please restart the application.")
    st.stop()
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
            if check_doctor_already_exists(session, username_input):
                st.error("Username already exists. Please choose another.")
            else:
                try:
                    doctor = register_doctor(session, username_input, password_input_1)
                    if doctor:
                        st.success("Registration successful! You can now log in.")
                        time.sleep(1)
                        st.switch_page("pages/login.py")
                    else:
                        st.error("Registration failed. Please try again.")
                except DuplicateEntryError:
                    st.error("Username already exists. Please choose another.")
                except DatabaseError:
                    st.error("A database error occurred. Please try again later.")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
st.write("Already have an account?")
if st.button("Login"):
    st.switch_page("pages/login.py")
