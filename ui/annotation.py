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


class AnnotateMode(Enum):
    """Enumeration for annotation modes."""
    ANNOTATE = auto()
    VERIFY = auto()


def render_image_column(img_path, img_index, num_images, key_prefix):
    """Render a column with an image and navigation controls."""
    img = Image.open(img_path)
    st.image(img)
    col1, col2 = st.columns([6, 2])
    with col1:
        if st.button("⬅️ Previous", key=f"prev_{key_prefix}"):
            return (img_index - 1) % num_images
    with col2:
        if st.button("Next ➡️", key=f"next_{key_prefix}"):
            return (img_index + 1) % num_images
    slider_val = st.slider(
        "Jump to image", 1, num_images, img_index + 1, key=f"slider_{key_prefix}"
    )
    if slider_val - 1 != img_index:
        return slider_val - 1
    return img_index


def render_metadata_panel(app, mode):
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

    acol1, acol2 = st.columns([1, 1])
    with acol1:
        st.session_state.setdefault("show_metadata", False)
        if st.button("Toggle Patient Metadata", key="toggle_metadata"):
            st.session_state.show_metadata = not st.session_state.show_metadata
    with acol2:
        if mode == AnnotateMode.VERIFY:
            st.session_state.setdefault("show_labels", False)
            if st.button("Toggle Labeler's Opinions", key="toggle_labels"):
                st.session_state.show_labels = not st.session_state.show_labels

    st.markdown("### Patient Metadata")
    if st.session_state["show_metadata"]:
        st.dataframe(df, use_container_width=True)

    if st.session_state["show_labels"]:
        if app.current_set.labeler_opinion is not None:
            st.dataframe(
                app.current_set.labeler_opinion,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("No labeler's opinions available for this set.")


def render_evaluation_controls(app, num_images):
    """Render the controls for technical evaluation and therapeutic markings."""
    st.markdown("### Technical Evaluation and Therapeutic Markings")
    bcol1, bcol2, bcol3, bcol4 = st.columns(4)
    with bcol1:
        if st.button("Irrelevant Data", key="irrelevant"):
            app.current_set.irrelevance ^= 1
        if app.current_set.irrelevance:
            st.warning("Marked as Irrelevant")
    with bcol2:
        if st.button("Low Quality", key="low_quality"):
            app.current_set.disquality ^= 1
        if app.current_set.disquality:
            st.warning("Marked as Low Quality")
    with bcol3:
        app.current_set.opinion_basel = st.number_input(
            "Basel Ganglia:", 1, num_images, app.current_set.opinion_basel
        )
    with bcol4:
        app.current_set.opinion_corona = st.number_input(
            "Corona Radiata:", 1, num_images, app.current_set.opinion_corona
        )


def render_navigation_controls(app, mode):
    """Render the navigation controls for the annotation phase."""
    ccol1, ccol2 = st.columns([1, 1])
    with ccol1:
        if st.button("Previous Set", key="prev_set"):
            app.set_index = (app.set_index - 1) % app.num_train_sets
            app.current_set = app.current_annotation_sets[app.set_index]
            st.rerun()
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
        target_page = Page.GREETING if mode == AnnotateMode.ANNOTATE else Page.TESTING
        if can_transition(app.page, target_page):
            app.update_scan_metadata(app.current_annotation_sets)
            app.page = Page.GREETING
            st.session_state.confirmed = False
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
        app.current_set.image_index_1 = render_image_column(
            img_path_1, app.current_set.image_index_1, num_images, "img_1"
        )
    with col2:
        app.current_set.image_index_2 = render_image_column(
            img_path_2, app.current_set.image_index_2, num_images, "img_2"
        )
    with col3:
        render_metadata_panel(app, mode)
        render_evaluation_controls(app, num_images)
        render_navigation_controls(app, mode)
