import streamlit as st
from app_state import AppState, Page, can_transition
from utils.credential_manager import CredentialManager


def registration(app: AppState, cm: CredentialManager) -> None:
    """Display the registration page."""
    if not cm:
        st.error("Credential Manager is not initialized.")
        return
    st.title("Register a New User")
    username_input = st.text_input("Username:")
    password_input_1 = st.text_input("Password:", type="password")
    password_input_2 = st.text_input("Confirm Password:", type="password")
    option = st.selectbox(
    "Role:",
    ["Verifier", "Labeler"]
)
    if st.button("Register", key="register_button"):
        # Validate input
        if not username_input or not password_input_1 or not password_input_2:
            st.error("Please fill out all fields.")
        elif password_input_1 != password_input_2:
            st.error("Passwords do not match.")
        else:
            # Try adding user
            success = cm.add_user(username_input, password_input_1, option)
            if success:
                st.success(f"User '{username_input}' registered successfully!")
                # Set app state to redirect to login next run
                if can_transition(app.page, Page.GREETING):
                    app.page = Page.GREETING
                    app.logon = False
                    st.rerun()
            else:
                st.error(f"User '{username_input}' already exists.")