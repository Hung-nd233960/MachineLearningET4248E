"""Display the greeting page for user login and registration."""

import streamlit as st
from app_state import AppState, Page, can_transition
from utils.credential_manager import CredentialManager


def greeting(app: AppState, cm: CredentialManager) -> None:
    """Display the greeting page."""
    app.set_greeting()
    st.title("Welcome to MedFabric - Collaborative Intelligence")
    username_input = st.text_input("Username:")
    password_input = st.text_input("Password:", type="password")
    if st.button("Login"):
        if not username_input or not password_input:
            st.error("Please enter both username and password.")
        else:
            if cm.verify_user(username_input, password_input):
                app.doctor_id = cm.get_user_id(username_input)
                app.doctor_role = cm.get_user_role(cm.get_username_by_id(app.doctor_id))
                st.success(f"Welcome back, {username_input}!")
                print(f"Doctor ID: {app.doctor_id}")
                app.logon = True
                if can_transition(app.page, Page.DASHBOARD):
                    app.page = Page.DASHBOARD
                    st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")

    if st.button("Register", key="register_redirect"):
        if can_transition(app.page, Page.REGISTRATION):
            app.page = Page.REGISTRATION
            st.rerun()
