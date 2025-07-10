# pylint: disable = C0121
"""Dashboard module for displaying and managing labeling progress.

This module handles the visualization and interaction with
patient annotation progress, self-labeled data, and verification
requests in the MedFabric annotation system.
"""

from typing import Tuple, Dict, Union, TypeAlias
import streamlit as st
import pandas as pd

from app_state import AppState, can_transition, Page

from utils.scan_metadata import undo_doctor_columns
from utils.dashboard.dashboard_info import dashboard_info
from utils.dashboard.choose_annotation_data import choose_annotation_data

ColumnConfig : TypeAlias = Dict[str, Union[st.column_config.TextColumn,
                                           st.column_config.NumberColumn,
                                           st.column_config.CheckboxColumn]]

# Column configuration for displaying self-labeled data
config_self = {
    "Scan Type": st.column_config.TextColumn(
        label=None, disabled=True, pinned=True, help="Type of scan performed"
    ),
    "Patient ID": st.column_config.TextColumn(
        label=None, disabled=True, pinned=True, help="Unique identifier for the patient"
    ),
    "Number of Images": st.column_config.NumberColumn(
        label=None, disabled=True, pinned=True, help="Number of images in the scan"
    ),
    "Number of Ratings": st.column_config.NumberColumn(
        label=None,
        disabled=True,
        pinned=True,
        help="Number of all ratings (labeled or verified)",
    ),
}
def create_config(role: str) -> ColumnConfig:
    """Create column configuration for the editable dashboard based on user role."""
    # Column configuration for editable dashboard
    if role == "Verifier".lower():
        action:str = "Verify"
    else:
        action:str = "Label"
    config_edited = {
        "Scan Type": st.column_config.TextColumn(
            label=None, disabled=True, pinned=True, help="Type of scan performed"
        ),
        "Patient ID": st.column_config.TextColumn(
            label=None, disabled=True, pinned=True, help="Unique identifier for the patient"
        ),
        "Number of Images": st.column_config.NumberColumn(
            label="Slices", disabled=True, pinned=False, help="Number of images in the scan"
        ),
        "Number of Ratings": st.column_config.NumberColumn(
            label="Ratings",
            disabled=True,
            pinned=False,
            help="Number of all ratings (labeled or verified)",
        ),
        "Labeled By Others": st.column_config.CheckboxColumn(
            label="Labeled",
            disabled=True,
            pinned=False,
            help="Indicates if the patient has been labeled " "by other doctors",
        ),
        "Verified By Others": st.column_config.CheckboxColumn(
            label="Verified",
            disabled=True,
            pinned=False,
            help="Indicates if the patient has been verified " "by other doctors",
        ),
        "Verify": st.column_config.CheckboxColumn(
            label=action,
            disabled=False,
            help=f"Click to {action.lower()} the patient. This will update "
            "the status of the patient to verified.",
        ),
    }
    return config_edited



def progress_counter(df: pd.DataFrame, uuid: str) -> Tuple[int, int, float]:
    """Calculate the labeling progress for a specific user (UUID)."""
    uuid_columns = [col for col in df.columns if uuid in col]

    if not uuid_columns:
        return 0, len(df), 0.0

    satisfied_rows = df[uuid_columns].notna().all(axis=1)
    progress_value = satisfied_rows.sum() / len(df) if len(df) > 0 else 0.0
    return satisfied_rows.sum(), len(df), progress_value


def get_progress_summary(df: pd.DataFrame, uuid: str) -> Tuple[int, int, float]:
    """Get the progress summary for the dashboard."""
    return progress_counter(df, uuid)


def get_dashboard_data(
    df: pd.DataFrame, uuid: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Get the self-labeled and remaining patients for the dashboard."""
    return dashboard_info(df, uuid)


def get_verification_selection(edited_data: pd.DataFrame) -> pd.DataFrame:
    """Get the patients selected for verification."""
    if "Verify" in edited_data.columns:
        return edited_data[edited_data["Verify"] == True]
    return pd.DataFrame()


def submit_verification_request(selected_patients: pd.DataFrame) -> bool:
    """Submit a verification request for the selected patients."""
    if not selected_patients.empty:
        st.success("Verification requested for the selected patients.")
    else:
        st.error(
            "No patients selected for verification. "
            "Please select at least one patient."
        )
    return not selected_patients.empty


def render_self_labeled_section(df: pd.DataFrame) -> None:
    """Render the section for self-labeled patients."""
    st.subheader("Self-Labeled Patients")
    if df.empty:
        st.write("You have not labeled any patients yet or there are no patients.")
    else:
        st.dataframe(
            df,
            column_config=config_self,
            use_container_width=True,
            column_order=[
                "Scan Type",
                "Patient ID",
                "Number of Images",
                "Number of Ratings",
            ],
            hide_index=True,
        )


def render_remaining_section(df: pd.DataFrame, config: ColumnConfig) -> pd.DataFrame:
    """Render the section for remaining patients to be labeled."""
    st.subheader("Remaining Patients")
    if df.empty:
        st.write("You have labeled all patients or there are no patients.")
        return pd.DataFrame()

    if st.toggle("Enable editing"):
        return st.data_editor(
            data=df,
            column_config=config,
            use_container_width=True,
            disabled=[
                "Scan Type",
                "Patient ID",
                "Number of Images",
                "Number of Ratings",
                "Labeled By Others",
                "Verified By Others",
            ],
            column_order=[
                "Scan Type",
                "Patient ID",
                "Number of Images",
                "Number of Ratings",
                "Labeled By Others",
                "Verified By Others",
                "Verify",
            ],
            hide_index=True,
        )
    st.dataframe(
        df,
        column_config=config,
        use_container_width=True,
        column_order=[
            "Scan Type",
            "Patient ID",
            "Number of Images",
            "Number of Ratings",
            "Labeled By Others",
            "Verified By Others",
            "Verify",
        ],
        hide_index=True,
    )
    return pd.DataFrame()


def render_verification_section(selected_patients: pd.DataFrame, config: ColumnConfig) -> bool:
    """Render the section for verifying selected patients."""
    st.subheader("Verification")

    if selected_patients.empty:
        st.warning("No patients selected for verification.")
    else:
        st.write("You have selected the following patients for verification:")
        st.dataframe(
            selected_patients,
            column_config=config,
            use_container_width=True,
            column_order=[
                "Scan Type",
                "Patient ID",
                "Number of Images",
                "Number of Ratings",
                "Labeled By Others",
                "Verified By Others",
            ],
            hide_index=True,
        )
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Submit Verification Request"):
            return submit_verification_request(selected_patients)
    with col2:
        if st.button("Return"):
            st.session_state["nuke"] = True
            st.rerun()
    return False


def dashboard(app: AppState) -> pd.DataFrame:
    """Display the dashboard page for user annotations."""
    st.title("Dashboard")
    config_edited = create_config(app.doctor_role)
    # Progress bar
    labeled, total, progress = get_progress_summary(
        app.scan_metadata, str(app.doctor_id)
    )
    st.progress(
        value=progress,
        text=(f"Patients Labeled: {labeled} / {total} " f"({progress * 100:.2f}%)"),
    )

    # Dashboard data
    self_label, remaining = get_dashboard_data(app.scan_metadata, str(app.doctor_id))

    # Layout
    col1, col2 = st.columns([1, 1])
    with col1:
        tab1, tab2 = st.tabs(["Self-Labeled", "Remaining Patients"])
        with tab1:
            render_self_labeled_section(self_label)
        with tab2:
            edited_data = render_remaining_section(remaining, config_edited)
            if "confirm_delete" not in st.session_state:
                st.session_state.confirm_delete = False

            if st.button("Delete all annotations", key="delete_annotations"):
                st.session_state.confirm_delete = True

            if st.session_state.confirm_delete:
                st.error(
                    "This will delete all your annotations. "
                    "Are you sure you want to proceed?"
                )
                if st.button("Confirm Deletion"):
                    app.scan_metadata = undo_doctor_columns(
                        app.scan_metadata, str(app.doctor_id)
                    )
                    st.success("All your annotations have been deleted.")
                    st.session_state.confirm_delete = False  # Reset confirmation flag
                    st.rerun()

    with col2:
        selected = get_verification_selection(edited_data)
        if render_verification_section(selected, config_edited):
            if can_transition(app.page, Page.ANNOTATION):
                app.page = Page.ANNOTATION
                app.current_annotation_sets = choose_annotation_data(
                    df=app.scan_metadata, filter=selected
                )
                st.rerun()
