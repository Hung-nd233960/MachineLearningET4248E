"""Annotation Phase Screen
This module provides the UI for the annotation phase of the application, 
allowing users to annotate and verify medical images."""

from enum import Enum, auto
import os
import streamlit as st
from PIL import Image

from app_state import AppState, Page, can_transition
from utils.dialog import confirm_dialog
from utils.diagnosis_df import diagnosis_df
from utils.list_parser import get_annotation_error, AnnotateError

placeholder_text = "Eg: 1,3,5,6, 8-20"

class AnnotateMode(Enum):
    """Enumeration for annotation modes."""
    ANNOTATE = auto()
    VERIFY = auto()

def has_any_errors() -> bool:
    return any(
        error is not None
        for key in st.session_state.keys()
        if key.startswith("errors_")
        for error in st.session_state[key].values()
    )


def render_image_column(img_path: str, img_index: int, num_images: int, key_prefix: str):
    """Render a column with an image and navigation controls."""
    img = Image.open(img_path)
    st.image(img, caption=f"Image {img_index + 1}/{num_images}", use_container_width=True)

    # Slider first to avoid layout flicker
    slider_val = st.slider(
        "Jump to image", 1, num_images, img_index + 1, key=f"slider_{key_prefix}"
    )
    new_index = slider_val - 1

    col1, col2 = st.columns([6, 2])
    with col1:
        if st.button("⬅️ Previous", key=f"prev_{key_prefix}"):
            new_index = (img_index - 1) % num_images
    with col2:
        if st.button("Next ➡️", key=f"next_{key_prefix}"):
            new_index = (img_index + 1) % num_images

    return new_index

def render_metadata_panel(app: AppState, mode: AnnotateMode) -> None:
    """Render the metadata panel with patient information and controls."""
    st.write(f"Current Set: {app.set_index + 1} of {app.num_train_sets}")
    zcol1, zcol2 = st.columns([1, 1])
    zcol1.write(f"Patient ID: {app.current_set.patient_id}")
    zcol2.write(f"Scan Type: {app.current_set.scan_type}")

    metadata = {
        key: value
        for key, value in app.current_set.patient_metadata.items()
        if key not in ["patient_id", "Category"]
    }
    df = diagnosis_df(metadata)
    
    with st.expander("**Patient Metadata**", expanded=False):
        st.dataframe(df, use_container_width=True)

    if mode == AnnotateMode.VERIFY:
        with st.expander("Labeler Opinion", expanded=True):
            if app.current_set.labeler_opinion is not None:
                st.dataframe(
                    app.current_set.labeler_opinion,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.warning("No labeler's opinions available for this set.")

def render_evaluation_controls(app: AppState, num_images: int) -> None:
    """Render the controls for technical evaluation and therapeutic markings."""
    st.markdown("### Technical Evaluation and Therapeutic Markings")

    idx = app.set_index

    # Define keys and default values
    keys_with_defaults = {
        f"checkbox_irrelevant_{idx}": app.current_set.irrelevance,
        f"checkbox_disquality_{idx}": app.current_set.disquality,
        f"basel_img_{idx}": app.current_set.basel_image,
        f"basel_score_{idx}": app.current_set.basel_score,
        f"corona_img_{idx}": app.current_set.corona_image,
        f"corona_score_{idx}": app.current_set.corona_score,
        f"errors_{idx}": {"basel": None, "corona": None},
    }

    # Initialize session state
    for key, default in keys_with_defaults.items():
        st.session_state.setdefault(key, default)

    # Extract keys for easier access
    key_irre = f"checkbox_irrelevant_{idx}"
    key_disq = f"checkbox_disquality_{idx}"
    key_basel_img = f"basel_img_{idx}"
    key_basel_score = f"basel_score_{idx}"
    key_corona_img = f"corona_img_{idx}"
    key_corona_score = f"corona_score_{idx}"
    error_key = f"errors_{idx}"

    # UI: checkboxes
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Irrelevant Data", key=key_irre)
    with col2:
        st.checkbox("Low Quality", key=key_disq)

    # Helper function to render annotation section
    def render_annotation_section(label: str, key_img: str, key_score: str, error_field: str):
        img_input = st.text_input(f"{label} Images:", key=key_img, max_chars=100, placeholder=placeholder_text).strip()
        error = get_annotation_error(img_input, num_images) if img_input else None
        st.session_state[error_key][error_field] = error
        if error:
            render_annotation_errors(error)
        st.number_input(f"{label} Score:", min_value=0, max_value=5, step=1, key=key_score)

    # UI: text + number inputs
    col3, col4 = st.columns(2)
    with col3:
        render_annotation_section("Basel", key_basel_img, key_basel_score, "basel")
    with col4:
        render_annotation_section("Corona", key_corona_img, key_corona_score, "corona")

    # Sync back to model
    app.current_set.irrelevance = st.session_state[key_irre]
    app.current_set.disquality = st.session_state[key_disq]
    app.current_set.basel_image = st.session_state[key_basel_img]
    app.current_set.basel_score = st.session_state[key_basel_score]
    app.current_set.corona_image = st.session_state[key_corona_img]
    app.current_set.corona_score = st.session_state[key_corona_score]
    print(f"{app.current_set.patient_id} - Basel: {app.current_set.basel_image}, Corona: {app.current_set.corona_image}")

def render_annotation_errors(error: AnnotateError) -> None:
    """Render the error message for annotation input validation."""
    if error == AnnotateError.INVALID_SYNTAX:
        st.error("Invalid syntax! Please use a comma-separated list of numbers or ranges (e.g., 1,3,5-7).")
    elif error == AnnotateError.NOT_UNIQUE:
        st.error("Numbers must be unique! Please check your input.")
    elif error == AnnotateError.NOT_ORDERED:
        st.error("Numbers must be in ascending order! Please check your input.")
    elif error == AnnotateError.OUT_OF_BOUNDS:
        st.error("Numbers must be within the valid range! Please check your input.")
    elif error == AnnotateError.INVALID_RANGE:
        st.error("Invalid range specified! Please check your input.")

def render_navigation_controls(app: AppState, mode: AnnotateMode) -> None:
    """Render the navigation controls for the annotation phase."""
    ccol1, ccol2 = st.columns([1, 1])
    with ccol1:
        if st.button("Previous Set", key="prev_set"):
            app.set_index = (app.set_index - 1) % app.num_train_sets
            app.current_set = app.current_annotation_sets[app.set_index]
            st.rerun()
        if has_any_errors():
            st.warning("⚠️ Some annotations are invalid. Please correct them before confirming.")
        else:
            if st.button("✅ Confirm"):
                st.session_state.show_confirm_dialog = True

    with ccol2:
        if st.button("Next Set", key="next_set"):
            app.set_index = (app.set_index + 1) % app.num_train_sets
            app.current_set = app.current_annotation_sets[app.set_index]
            st.rerun()
        if st.button("Return") and can_transition(app.page, Page.GREETING):
            app.page = Page.GREETING
            st.rerun()

    if st.session_state.get("show_confirm_dialog", False):
        confirm_dialog()

    if st.session_state.get("confirmed", False):
        target_page = Page.GREETING
        if can_transition(app.page, target_page):
            app.update_scan_metadata(app.current_annotation_sets)
            st.session_state.confirmed = False
            st.session_state["nuke"] = True
            st.rerun()


def annotation_screen(app: AppState, mode: AnnotateMode) -> None:
    """Main function to render the annotation screen."""
    st.title("Annotation Phase")
    num_images = len(app.current_set.image_list)

    img_path_1 = os.path.join(
        app.current_set.folder,
        app.current_set.image_list[app.current_set.image_index_1],
    )
    img_path_2 = os.path.join(
        app.current_set.folder,
        app.current_set.image_list[app.current_set.image_index_2],
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        new_image_index_1 = render_image_column(
            img_path_1, app.current_set.image_index_1, num_images, "img_1"
        )
        if new_image_index_1 != app.current_set.image_index_1:
            app.current_set.image_index_1 = new_image_index_1
            st.rerun()
    with col2:
        new_image_index_2 = render_image_column(
            img_path_2, app.current_set.image_index_2, num_images, "img_2"
        )
        if new_image_index_2 != app.current_set.image_index_2:
            app.current_set.image_index_2 = new_image_index_2
            st.rerun()
    with col3:
        render_metadata_panel(app, mode)
        render_evaluation_controls(app, num_images)
        render_navigation_controls(app, mode)
