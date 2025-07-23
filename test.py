import streamlit as st
import pandas as pd

st.title("🔢 Interactive Weighted Average Calculator")

# Initialize session state for data
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "A": [10.0, 20.0],
        "B": [1.0, 2.0]
    })

st.subheader("📋 Editable Table")
st.data_editor(
    st.session_state.data,
    num_rows="dynamic",
    use_container_width=True,
    key="editor",
)

# Save changes
edited_df = st.session_state["editor"] 

# Calculate and display weighted average
try:
    if edited_df.empty:
        st.warning("Table is empty.")
    elif (edited_df["B"] == 0).all():
        st.error("All weights are zero — cannot divide.")
    else:
        weighted_sum = (edited_df["A"] * edited_df["B"]).sum()
        total_weight = edited_df["B"].sum()
        weighted_avg = weighted_sum / total_weight
        st.success(f"✅ Weighted Average: {weighted_avg:.4f}")
except Exception as e:
    st.error(f"Error: {e}")
