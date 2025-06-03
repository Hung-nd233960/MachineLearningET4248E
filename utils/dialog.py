# pylint: disable = missing-module-docstring
import streamlit as st

@st.dialog("Confirm Set")
def confirm_dialog():
    st.write("Are you sure you want to confirm this set?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes"):
            st.session_state.confirmed = True
            st.session_state.show_confirm_dialog = False
            st.rerun()

    with col2:
        if st.button("No"):
            st.session_state.show_confirm_dialog = False
            st.rerun()
