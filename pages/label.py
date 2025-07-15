from typing import List
import streamlit as st
from PIL import Image as PILImage
from utils.db import get_session
from utils.image_session import ImageSetEvaluationSession, ImageEvaluationSession
from utils.image_session import prepare_image_set_evaluation
from utils.models import Region
from utils.evaluation import add_or_update_image_evaluation, add_or_update_set_evaluation

st.set_page_config(
    page_title="Labeling Phase",
    page_icon=":pencil2:",
    layout="wide",
)
app = st.session_state
doctor_uuid = app.get("user")
selected_scans = app.get("selected_scans")
if not doctor_uuid:
    st.error("You must be logged in to access this page.")
    st.stop()
elif selected_scans is None:
    st.error("No scans selected for evaluation.")
    st.stop()


def reset():
    st.cache_data.clear()
    st.session_state.clear()
    st.switch_page("pages/login.py")


def save_annotations():
    conversion_dict = {
        "BasalGanglia": Region.BasalGanglia,
        "CoronaRadiata": Region.CoronaRadiata,
        None: Region.None_,
    }
    with get_session() as session:
        for set_ in app.labeling_session:
            add_or_update_set_evaluation(
                session,
                doctor_id=doctor_uuid,
                image_set_id=set_.image_set_id,
                low_quality=set_.low_quality,
                irrelevant=set_.irrelevant_data,
            )
            for img in set_.images:
                add_or_update_image_evaluation(
                    session,
                    doctor_id=doctor_uuid,
                    image_id=img.image_id,
                    image_set_id=set_.image_set_id,
                    region=conversion_dict[img.region],
                    basal_score=img.score if img.region == "BasalGanglia" else None,
                    corona_score=img.score if img.region == "CoronaRadiata" else None,
                )
        session.commit()
    st.success("Annotations saved successfully.")


@st.cache_data
def prepare_labeling_session(
    _session, doctor_id: str = doctor_uuid, list_scan: List[str] = selected_scans
) -> List[ImageSetEvaluationSession]:
    with get_session() as session:
        img_set_sessions = []
        for scan_id in list_scan:
            img_set_eval = prepare_image_set_evaluation(session, doctor_id, scan_id)
            if img_set_eval:
                img_set_sessions.append(img_set_eval)
            else:
                st.warning(f"No evaluations found for scan {scan_id}.")
        return img_set_sessions


def render_metadata_panel(
    set_index, num_sets, patient_id, scan_type, patient_df, labeler_opinion
) -> None:
    
    """Render the metadata panel with patient information and controls."""
    acol1, acol2 = st.columns([1, 1])
    with acol1:
        st.write(f"Current Set: {set_index + 1} of {num_sets}")
    with acol2:
        new_set_index = render_set_column(
        set_index=app.session_index,
        num_sets=len(app.labeling_session),
        key_prefix="set_column",
    )
        if new_set_index != app.session_index:
            app.session_index = new_set_index
            app.current_session = (
                app.labeling_session[app.session_index] if app.labeling_session else None
            )
            st.rerun()

    zcol1, zcol2 = st.columns([1, 1])
    zcol1.write(f"Patient ID: {patient_id}")
    zcol2.write(f"Scan Type: {scan_type}")

    with st.expander("**Patient Metadata**", expanded=False):
        st.dataframe(patient_df, use_container_width=True, hide_index=True)

    with st.expander("Labeler Opinion", expanded=True):
        if labeler_opinion is not None:
            st.dataframe(
                labeler_opinion,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("No labeler's opinions available for this set.")


def render_image_column(
    img_path: str, img_index: int, num_images: int
):
    """Render a column with an image and navigation controls."""
    img = PILImage.open(img_path)
    st.image(
        img, caption=f"Image {img_index + 1}/{num_images}", use_container_width=True
    )

def render_image_navigation_controls(num_images: int, img_index: int, key_prefix: str) -> int:
    """Render navigation controls for image selection."""
    # Slider first to avoid layout flicker
    acol1, acol2, acol3 = st.columns([2, 1, 1])
    with acol1:
        slider_val = st.slider(
            "Jump to image", 1, num_images, img_index + 1, key=f"slider_{key_prefix}"
        )
        new_index = slider_val - 1

    with acol2:
        if st.button("Previous", key=f"prev_{key_prefix}"):
            new_index = (img_index - 1) % num_images
    with acol3:
        if st.button("Next", key=f"next_{key_prefix}"):
            new_index = (img_index + 1) % num_images

    return new_index


def render_set_column(set_index: int, num_sets: int, key_prefix: str):
    """Render a column with set navigation controls."""
    col1, col2 = st.columns([1, 1])
    new_index = set_index
    with col1:
        if st.button("Previous Set", key=f"prev_set_{key_prefix}"):
            new_index = (set_index - 1) % num_sets
    with col2:
        if st.button("Next Set", key=f"next_set_{key_prefix}"):
            new_index = (set_index + 1) % num_sets

    return new_index


def render_image_region_controls() -> None:
    idx = app.current_session.current_index
    # Define keys and default values
    if app.current_session.images[idx].region == "None":
        default_ = None
    else:
        default_ = app.current_session.images[idx].region
    keys_with_defaults = {
        f"segmented_control_{idx}_{app.current_session.image_set_id}": default_
    }
    # Initialize session state
    for key, default in keys_with_defaults.items():
        st.session_state.setdefault(key, default)

    # Extract keys for easier access
    key_region = f"segmented_control_{idx}_{app.current_session.image_set_id}"

    options = ["BasalGanglia", "CoronaRadiata"]

    st.segmented_control(
        options=options,
        key=key_region,
        format_func=lambda s: "".join(
            [" " + c if c.isupper() and i != 0 else c for i, c in enumerate(s)]
        ),
        label="Region:",
        selection_mode="single",
    )
    if app.current_session.images[idx].region != st.session_state[key_region]:
        if app.current_session.images[idx].region is None:
            app.current_session.images[idx].score = None
        else:
            app.current_session.images[idx].score = 0
    app.current_session.images[idx].region = st.session_state[key_region]
    print(f"Selected region: {app.current_session.images[idx].region}")


def render_image_score_controls() -> None:
    idx = app.current_session.current_index
    # Define keys and default values
    keys_with_defaults = {
        f"score_{idx}_{app.current_session.image_set_id}": app.current_session.images[
            idx
        ].score,
    }
    # Initialize session state
    for key, default in keys_with_defaults.items():
        st.session_state.setdefault(key, default)

    # Extract keys for easier access
    key = f"score_{idx}_{app.current_session.image_set_id}"

    if app.current_session.images[idx].region == "BasalGanglia":
        st.number_input(
            "Basal Ganglia Score (0-4):",
            min_value=0,
            max_value=4,
            key=key,
        )
    elif app.current_session.images[idx].region == "CoronaRadiata":
        st.number_input(
            "Corona Radiata Score (0-6):",
            min_value=0,
            max_value=6,
            key=key,
        )
    # Sync back to model
    app.current_session.images[idx].score = st.session_state[key]


def render_set_evaluation_controls() -> None:
    """Render the controls for technical evaluation and therapeutic markings."""
    st.markdown("### Image Set Evaluation")

    idx = app.session_index

    # Define keys and default values
    keys_with_defaults = {
        f"checkbox_irrelevant_{idx}": app.current_session.irrelevant_data,
        f"checkbox_disquality_{idx}": app.current_session.low_quality,
    }

    # Initialize session state
    for key, default in keys_with_defaults.items():
        st.session_state.setdefault(key, default)

    # Extract keys for easier access
    key_irre = f"checkbox_irrelevant_{idx}"
    key_disq = f"checkbox_disquality_{idx}"
    # UI: checkboxes
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Irrelevant Data", key=key_irre)
    with col2:
        st.checkbox("Low Quality", key=key_disq)

    # Sync back to model
    app.current_session.irrelevant_data = st.session_state[key_irre]
    app.current_session.low_quality = st.session_state[key_disq]


def check_annotate_completely() -> bool:
    def check_image_annotations_complete(images: List[ImageEvaluationSession]) -> bool:
        has_basal = any(
            img.region == "BasalGanglia" and img.score is not None for img in images
        )
        has_corona = any(
            img.region == "CoronaRadiata" and img.score is not None for img in images
        )
        return has_basal and has_corona

    for set_ in app.labeling_session:
        if set_.irrelevant_data or set_.low_quality:
            continue
        if not check_image_annotations_complete(set_.images):
            return False
    return True


st.title("Annotation Phase")
with get_session() as session:
    if "labeling_session" not in app:
        app.labeling_session = prepare_labeling_session(
            get_session(), doctor_uuid, selected_scans
        )
        app.session_index = 0
        app.current_session = (
            app.labeling_session[app.session_index] if app.labeling_session else None
        )
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    img_path = app.current_session.images[app.current_session.current_index].image_path
    render_image_column(
        img_path=img_path,
        img_index=app.current_session.current_index,
        num_images=len(app.current_session.images),
    )

with col2:
    with st.expander("## Image Navigation", expanded=True):
        new_image_index = render_image_navigation_controls(
            num_images=len(app.current_session.images),
            img_index=app.current_session.current_index,
            key_prefix="image_navigation")
        if new_image_index != app.current_session.current_index:
            app.current_session.current_index = new_image_index
            st.rerun()

    idx = app.session_index
    key_irre = f"checkbox_irrelevant_{idx}"
    key_disq = f"checkbox_disquality_{idx}"
    if app.get(key_irre, False) or app.get(key_disq, False):
        st.warning(
            "You cannot annotate images when the set is marked as irrelevant or low quality."
        )
    else:
        with st.expander("## Current Image Evaluation", expanded=True):
            acol1, acol2 = st.columns([1, 1])
            with acol1:
                render_image_region_controls()
            with acol2:
                if app.current_session.images[app.current_session.current_index].region:
                    render_image_score_controls()


with col3:
    render_metadata_panel(
        set_index=app.session_index,
        num_sets=len(app.labeling_session),
        patient_id=app.current_session.patient_id,
        scan_type=app.current_session.image_set_id,
        patient_df=app.current_session.patient_diagnosis,
        labeler_opinion=None,
    )
    render_set_evaluation_controls()
    
    if not check_annotate_completely():
        st.warning("Please complete all image annotations before proceeding.")
    else:
        if st.button("Confirm Annotations"):
            save_annotations()
            with get_session() as session:
                from utils.conflict import (
                    scan_and_update_image_set_conflicts,
                    flag_conflicted_image_sets,
                )
                scan_and_update_image_set_conflicts(session)
                flag_conflicted_image_sets(session)
            reset()
