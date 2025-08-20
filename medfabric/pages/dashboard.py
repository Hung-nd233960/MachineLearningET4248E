from typing import Tuple
import time
import streamlit as st
import pandas as pd
from utils.db.models import Evaluation, ImageSet
from utils.db.database import get_session

st.set_page_config(
    page_title="Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)


@st.cache_data
def get_image_sets_with_evaluation_status(doctor_uuid: str, _session) -> pd.DataFrame:
    """
    Return a DataFrame of all image sets with evaluation status by the doctor.

    Columns: scan_id, patient_id, num_images, conflicted, editing, evaluated (bool)
    """
    # Step 1: Get image_set_ids this doctor has evaluated
    evaluated_ids = (
        _session.query(Evaluation.image_set_id)
        .filter(Evaluation.doctor_id == doctor_uuid)
        .distinct()
        .all()
    )
    evaluated_ids = {row[0] for row in evaluated_ids}  # set for fast lookup

    # Step 2: Get all image sets
    all_image_sets = _session.query(ImageSet).all()

    # Step 3: Build DataFrame with evaluation status
    df = pd.DataFrame(
        [
            {
                "scan_id": imgset.image_set_id,
                "patient_id": imgset.patient_id,
                "num_images": imgset.num_images,
                "conflicted": imgset.conflicted,
                "evaluated": imgset.image_set_id in evaluated_ids,
                "edit": False,
            }
            for imgset in all_image_sets
        ]
    )

    return df


@st.cache_data
def get_image_set_evaluation_progress(
    doctor_uuid: str, _session
) -> Tuple[int, int, float]:
    """
    Return progress info of image sets evaluated by a doctor:
    - evaluated_count: how many image sets this doctor has evaluated
    - total_count: total number of image sets in the system
    - percent: evaluated / total (as float ratio, rounded to 2 decimals)
    """
    total_count = _session.query(ImageSet).count()

    evaluated_set_ids = (
        _session.query(Evaluation.image_set_id)
        .filter(Evaluation.doctor_id == doctor_uuid)
        .distinct()
        .all()
    )
    evaluated_count = len(evaluated_set_ids)

    percent = round(evaluated_count / total_count, 2) if total_count else 0.0

    return evaluated_count, total_count, percent


# Column configuration for displaying self-labeled data
config_self = {
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
    "conflicted": st.column_config.CheckboxColumn(
        label="Conflicted",
        disabled=True,
        help="Indicates if the scan has unresolved conflicts",
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

config_chosen = {
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
    "conflicted": st.column_config.CheckboxColumn(
        label="Conflicted",
        disabled=True,
        help="Indicates if the scan has unresolved conflicts",
    ),
    "evaluated": st.column_config.CheckboxColumn(
        label="Evaluated",
        disabled=True,
        help="Indicates if the scan has been evaluated by you",
    ),
}
doctor_uuid = st.session_state.get("user")
if not doctor_uuid:
    st.error("You must be logged in to view this information.")
else:
    st.set_page_config(
        page_title="Dashboard",
        page_icon=":bar_chart:",
        layout="wide",
    )
    st.title("Dashboard")
    with get_session() as session:
        df = get_image_sets_with_evaluation_status(doctor_uuid, session)
        evaluated_count, total_count, progress = get_image_set_evaluation_progress(
            doctor_uuid, session
        )
    st.progress(
        value=progress,
        text=(
            f"Patients Labeled: {evaluated_count} / {total_count} "
            f"({progress * 100:.2f}%)"
        ),
    )
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Choose scans to evaluate")
        edited_data = st.data_editor(
            data=df,
            use_container_width=True,
            column_config=config_self,
            disabled=["scan_id", "patient_id", "num_images", "conflicted", "evaluated"],
            column_order=[
                "scan_id",
                "patient_id",
                "num_images",
                "conflicted",
                "evaluated",
                "edit",
            ],
            hide_index=True,
            key="evaluated_image_sets",
        )
    with col2:
        selected_scans = edited_data[edited_data["edit"]]
        if not selected_scans.empty:
            st.subheader("Selected Scans for Evaluation")
            st.dataframe(
                selected_scans.drop(columns=["edit"]),
                use_container_width=True,
                hide_index=True,
                column_config=config_chosen,
            )
            st.write(f"You have chosen {len(selected_scans)} scans for evaluation.")
            if st.button("Evaluate Selected Scans"):
                # Store selected scans in session state for further processing
                st.session_state.selected_scans = selected_scans["scan_id"].tolist()
                st.success(
                    f"Selected {len(st.session_state.selected_scans)} scans for evaluation."
                )
                time.sleep(1)
                st.switch_page("pages/label.py")
        else:
            st.subheader("No Scans Selected")
            st.write("Please select scans to evaluate by checking the 'Evaluate' box.")
