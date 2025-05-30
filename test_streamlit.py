import streamlit as st
from streamlit_extras.stoggle import stoggle
from streamlit_extras.stateful_button import button

def example():
    if button("Button 1", key="button1"):
        st.write("Button 1 clicked!")

example()
