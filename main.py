import streamlit as st

pg = st.navigation(
    [
        st.Page("pages/login.py"),
        st.Page("pages/register.py"),
        st.Page("pages/dashboard.py"),
        st.Page("pages/label.py"),
    ]
)
pg.run()
