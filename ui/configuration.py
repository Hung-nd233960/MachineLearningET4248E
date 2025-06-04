import streamlit as st
from app_state import AppState, Page, can_transition
from utils.credential_manager import CredentialManager

def configuration(app: AppState, cm: CredentialManager) -> None:
    """Display the configuration page."""
    st.title("Configuration")
    if cm.get_user_role(app.doctor_id) == "verifier":
        num_train_sets = st.number_input("Number of Training Sets", min_value=1, max_value=10, value=5)
        num_test_sets = st.number_input("Number of Test Sets", min_value=1, max_value=10, value=5)
        if st.button("Save Configuration"):
            app.num_train_sets = num_train_sets
            app.num_test_sets = num_test_sets
            st.success("Configuration saved successfully!")
            if can_transition(app.page, Page.VERIFICATION):
                app.page = Page.VERIFICATION
                st.rerun()
    elif cm.get_user_role(app.doctor_id) == "labeler":
        num_train_sets = st.number_input("Number of Training Sets", min_value=1, max_value=10, value=5)
        if st.button("Save Configuration"):
            app.num_train_sets = num_train_sets
            st.success("Configuration saved successfully!")
            if can_transition(app.page, Page.ANNOTATION):
                app.page = Page.ANNOTATION
                st.rerun()
    