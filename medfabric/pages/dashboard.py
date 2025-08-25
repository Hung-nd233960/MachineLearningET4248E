from typing import Tuple
import uuid as uuid_lib
import time
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from medfabric.api.errors import EmptyDatasetError
from medfabric.api.image_set_input import get_all_image_sets, exist_any_image_set
from medfabric.api.get_evaluated_sets import get_doctor_image_sets
from medfabric.pages.dashboard.dashboard_config import (
    config_self,
    config_chosen,
)

st.set_page_config(
    page_title="Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)


@st.cache_data
def get_image_sets_with_evaluation_status(
    _db_session: Session, doctor_uuid: uuid_lib.UUID
) -> Tuple[pd.DataFrame, int, int, float]:
    """
    Retrieve a DataFrame containing image sets along with their evaluation status by a specific doctor.

    This function fetches all image sets from the database,
    determines which of them have been evaluated by the specified doctor,
    and constructs a DataFrame with relevant details.
    Additionally, it calculates the total number of image sets, the number of evaluated image sets, and the percentage of evaluated image sets.

    Args:
        doctor_uuid (uuid_lib.UUID): The unique identifier of the doctor.

    Returns:
        Tuple[pd.DataFrame, int, int, float]: A tuple containing:
            - A pandas DataFrame with columns:
                - scan_id (str): The unique identifier of the image set.
                - patient_id (str): The unique identifier of the patient.
                - num_images (int): The number of images in the image set.
                - evaluated (bool): Whether the image set has been evaluated by the doctor.
                - edit (bool): Placeholder column, currently set to False.
            - The number of evaluated image sets (int).
            - The total number of image sets (int).
            - The percentage of evaluated image sets (float), rounded to two decimal places.


    """
    # Step 1: Get image_set_ids this doctor has evaluated
    evaluated_ids = get_doctor_image_sets(_db_session, doctor_uuid)
    # Step 2: Get all image sets
    all_image_sets = get_all_image_sets(_db_session)
    if all_image_sets is None:
        raise EmptyDatasetError("No image sets found in the database.")
    # Step 3: Build DataFrame with evaluation status
    df = pd.DataFrame(
        [
            {
                "index": imgset.index,
                "scan_id": imgset.image_set_id,
                "patient_id": imgset.patient_id,
                "num_images": imgset.num_images,
                "evaluated": imgset.image_set_id in evaluated_ids,
                "edit": False,
            }
            for imgset in all_image_sets
        ]
    )
    total_count = len(df)
    evluated_count = len(evaluated_ids)
    percent = round(evluated_count / total_count, 2) if total_count else 0.0
    return df, evluated_count, total_count, percent


# Column configuration for displaying self-labeled data

doctor_uuid = st.session_state.get("user")
doctor_session = st.session_state.get("user_session")
st.set_page_config(
    page_title="Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)
db_session = st.session_state.get("db_session")
if doctor_uuid is None:
    st.error("You must be logged in to view this information.")
    st.stop()
elif doctor_session is None:
    st.error("User session not found. Please log in again.")
    st.stop()
elif "db_session" not in st.session_state or db_session is None:
    st.error("Database session not found. Please restart the application.")
    st.stop()
elif not exist_any_image_set(db_session):
    st.error("Error retrieving image sets. Please contact the maintainer.")
    st.stop()
else:
    st.title("Dashboard")

    df, evaluated_count, total_count, progress = get_image_sets_with_evaluation_status(
        db_session, doctor_uuid
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
            disabled=[
                "index",
                "scan_id",
                "patient_id",
                "num_images",
                "evaluated",
            ],
            column_order=[
                "index",
                "scan_id",
                "patient_id",
                "num_images",
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
