import streamlit as st
from app_state import AppState, Page, can_transition

def configuration(app: AppState) -> None:
    """Display the configuration page."""
    st.title("Configuration")
    num_train_sets = st.number_input("Number of Training Sets", min_value=1, max_value=10, value=5)
    num_test_sets = st.number_input("Number of Test Sets", min_value=1, max_value=10, value=5)
    if st.button("Save Configuration"):
        app.num_train_sets = num_train_sets
        app.num_test_sets = num_test_sets
        st.success("Configuration saved successfully!")
        if can_transition(app.page, Page.TRAINING):
            app.page = Page.TRAINING
            st.rerun()
    