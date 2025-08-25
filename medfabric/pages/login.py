import logging
import streamlit as st
from medfabric.api.credentials import login_doctor
from medfabric.api.errors import (
    UserNotFoundError,
    InvalidCredentialsError,
    DatabaseError,
)
from medfabric.api.sessions import create_session

st.set_page_config(
    page_title="Login",
    page_icon=":key:",
    layout="centered",
)
session = st.session_state.get("db_session")
if session is None:
    st.error("Database session not found. Please restart the application.")
    st.stop()
with st.form("login_form", clear_on_submit=True, enter_to_submit=True, border=True):
    st.title("Login to MedFabric")
    username_input = st.text_input("Username:")
    password_input = st.text_input("Password:", type="password")

    if st.form_submit_button("Login"):
        if not username_input or not password_input:
            st.error("Please enter both username and password.")
        try:
            doctor = login_doctor(session, username_input, password_input)
            if doctor:
                st.success("Login successful")

                # e.g., store in session_state
                st.session_state.user = doctor.uuid
                logging.info(
                    "Doctor %s logged in with UUID %s", doctor.username, doctor.uuid
                )
                st.session_state.user_session = create_session(session, doctor.uuid)
                st.switch_page("pages/dashboard.py")
            else:
                st.error("Invalid username or password")
        except UserNotFoundError:
            st.error("User not found. Please check your username.")
        except InvalidCredentialsError:
            st.error("Invalid password. Please try again.")
        except DatabaseError:
            logging.exception("Database error during login for '%s'", username_input)
            st.error("A database error occurred. Please try again later.")
        except Exception as e:
            logging.exception("Unexpected error during login for '%s'", username_input)
            st.error(f"An unexpected error occurred: {str(e)}")
st.write("Don't have an account?")

if st.button("Register"):
    st.switch_page("pages/register.py")
