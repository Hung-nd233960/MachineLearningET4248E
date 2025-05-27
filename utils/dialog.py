import streamlit as st

@st.dialog(title="Confirm Set")
def confirm_dialog():
    st.write("Are you sure you want to confirm this set?")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Yes"):
            """
            app.update_scan_metadata([app.current_set])
            st.success("Set confirmed and metadata updated.")
            app.set_index = (app.set_index + 1) % app.num_train_sets
            app.current_set = app.current_training_sets[app.set_index]"""
            st.rerun()
    with col2:
        if st.button("No"):
            st.write("Confirmation cancelled.")
            st.rerun()
