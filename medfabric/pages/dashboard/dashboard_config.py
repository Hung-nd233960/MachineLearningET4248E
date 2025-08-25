import streamlit as st

st.session_state.config_self = {
    "index": st.column_config.NumberColumn(
        label="Index", disabled=True, pinned=True, help="Index of the scan"
    ),
    "scan_id": st.column_config.TextColumn(
        label="Scan Type", disabled=True, pinned=True, help="Type of scan performed"
    ),
    "patient_id": st.column_config.TextColumn(
        label="Patient ID",
        disabled=True,
        pinned=True,
        help="Unique identifier for the patient",
    ),
    "num_images": st.column_config.NumberColumn(
        label="Number of Images",
        disabled=True,
        pinned=True,
        help="Number of images in the scan",
    ),
    "evaluated": st.column_config.CheckboxColumn(
        label="Evaluated",
        disabled=True,
        help="Indicates if the scan has been evaluated by you",
    ),
    "edit": st.column_config.CheckboxColumn(
        label="Evaluate", disabled=False, help="Click to evaluate or edit this scan"
    ),
}

st.session_state.config_chosen = {
    "index": st.column_config.NumberColumn(
        label="Index", disabled=True, pinned=True, help="Index of the scan"
    ),
    "scan_id": st.column_config.TextColumn(
        label="Scan Type", disabled=True, pinned=True, help="Type of scan performed"
    ),
    "patient_id": st.column_config.TextColumn(
        label="Patient ID",
        disabled=True,
        pinned=True,
        help="Unique identifier for the patient",
    ),
    "num_images": st.column_config.NumberColumn(
        label="Number of Images",
        disabled=True,
        pinned=True,
        help="Number of images in the scan",
    ),
    "evaluated": st.column_config.CheckboxColumn(
        label="Evaluated",
        disabled=True,
        help="Indicates if the scan has been evaluated by you",
    ),
}
config_self = st.session_state.config_self
config_chosen = st.session_state.config_chosen
