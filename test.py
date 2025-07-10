import streamlit as st

# Initialize list once (only if not present)
if "list" not in st.session_state:
    st.session_state["list"] = [False] * 10
if "index" not in st.session_state:
    st.session_state["index"] = 0

# Toggle callback
def toggle():
    st.session_state["index"] = (st.session_state["index"] + 1) % len(st.session_state["list"])

# UI
st.button("Toggle", key="toggle_button", on_click=toggle)
i = st.session_state["index"]
st.write(f"Current index: {i + 1}")

# Key must be unique and stable — don't reassign the list directly
checkbox_key = f"checkbox_{i}"
st.session_state["list"][i] = st.checkbox(
    f"Option {i + 1}",
    value=st.session_state["list"][i],
    key=checkbox_key
)

# Display all current states
st.markdown(f"Your selected options: {st.session_state['list']}")
