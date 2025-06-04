from enum import Enum, auto
import os
import streamlit as st
from PIL import Image

from app_state import AppState, Page, can_transition
from utils.dialog import confirm_dialog
from utils.diagnosis_df import diagnosis_df

class AnnotateMode(Enum):
    """Enumeration for the annotation mode."""
    ANNOTATE = auto()
    VERIFY = auto()

def annotation_screen(app: AppState, mode: AnnotateMode) -> None:
    """Display the training phase screen."""
    st.title("Annotation Phase")            
    num_images = len(app.current_set.image_list)
    img_path_1 = os.path.join(app.current_set.folder,
                            app.current_set.image_list[app.current_set.image_index_1])
    img_path_2 = os.path.join(app.current_set.folder,
                            app.current_set.image_list[app.current_set.image_index_2])
    column1, column2, column3 = st.columns([1, 1, 1])
    with column1:
        img_1 = Image.open(img_path_1)
        st.image(img_1)
        col1, col2 = st.columns([6, 2])
        with col1:
            if st.button("⬅️ Previous", key="prev_img_1"):
                app.current_set.image_index_1 = (
                    app.current_set.image_index_1 - 1
                ) % num_images
                st.rerun()

        with col2:
            if st.button("Next ➡️", key="next_img_1"):
                app.current_set.image_index_1 = (
                    app.current_set.image_index_1 + 1
                ) % num_images
                st.rerun()

        slider_val = st.slider(
            "Jump to image", 1, num_images, app.current_set.image_index_1 + 1, key ="slider_img_1"
        )
        if slider_val - 1 != app.current_set.image_index_1:
            app.current_set.image_index_1 = slider_val - 1
            st.rerun()

    with column2:
        img_2 = Image.open(img_path_2)
        st.image(img_2)
        col1, col2 = st.columns([6, 2])
        with col1:
            if st.button("⬅️ Previous", key="prev_img_2"):
                app.current_set.image_index_2 = (
                    app.current_set.image_index_2 - 1
                ) % num_images
                st.rerun()

        with col2:
            if st.button("Next ➡️", key="next_img_2"):
                app.current_set.image_index_2 = (
                    app.current_set.image_index_2 + 1
                ) % num_images
                st.rerun()

        slider_val = st.slider(
            "Jump to image", 1, num_images, app.current_set.image_index_2 + 1, key ="slider_img_2"
        )
        if slider_val - 1 != app.current_set.image_index_2:
            app.current_set.image_index_2 = slider_val - 1
            st.rerun()

    with column3:
        st.write(f"Current Set: {app.set_index + 1} of {app.num_train_sets}")
        zcol1, zcol2 = st.columns([1, 1])
        with zcol1:
            st.write(f"Patient ID: {app.current_set.patient_id}")
        with zcol2:
            st.write(f"Scan Type: {app.current_set.scan_type}")
        
        acol1, acol2 = st.columns([1, 1])
        # Filter out unwanted keys
        metadata = {
            key: value
            for key, value in app.current_set.patient_metadata.items()
            if key != "patient_id" and key != "Category"
        }

        df = diagnosis_df(metadata)
        with acol1:
            if "show_metadata" not in st.session_state:
                st.session_state.show_metadata = False
            if st.button("Toggle Patient Metadata", key="toggle_metadata"):
                st.session_state.show_metadata = not st.session_state.show_metadata

            # Conditionally show the dataframe
            
        with acol2:
            if "show_labels" not in st.session_state:
                st.session_state.show_labels = False
            if st.button("Labeler's Opinions", key="toggle_labels"):
                st.session_state.show_labels = not st.session_state.show_labels

        if st.session_state.show_metadata:
                st.dataframe(df, use_container_width=True)
                
        if st.session_state.show_labels:
            if app.current_set.labeler_opinion is not None:
                st.dataframe(
                    app.current_set.labeler_opinion,
                    use_container_width=True,
                )
            else:
                st.warning("No labeler's opinions available for this set.")
    
        st.markdown("### Technical Evaluation and Theraputic Markings")
        bcol1, bcol2, bcol3, bcol4 = st.columns([1, 1, 1, 1])
        with bcol1:
            temp_irrelevance_button = st.button("Irrelevant Data", key="irrelevant")
            if temp_irrelevance_button and app.current_set.irrelevance == 0:
                app.current_set.irrelevance = 1
            elif temp_irrelevance_button and app.current_set.irrelevance == 1:
                app.current_set.irrelevance = 0
            if app.current_set.irrelevance == 1:
                st.warning("Marked as Irrelevant")
        with bcol2:
            temp_quality_button = st.button("Low Quality", key="low_quality")
            if temp_quality_button and app.current_set.disquality == 0:
                app.current_set.disquality = 1
            elif temp_quality_button and app.current_set.disquality == 1:
                app.current_set.disquality = 0
            if app.current_set.disquality == 1:
                st.warning(
                    "Marked as Low Quality")
        with bcol3:
            basel = st.number_input(
                "Basel Ganglia Image:",
                min_value=1,
                max_value=num_images,
                value=app.current_set.opinion_basel,
            )
            app.current_set.opinion_basel = basel

        with bcol4:
            thalamus = st.number_input(
                "Thalamus Image:",
                min_value=1,
                max_value=num_images,
                value=app.current_set.opinion_thalamus,
            )
            app.current_set.opinion_thalamus = thalamus

        ccol1, ccol2 = st.columns([1, 1])
        with ccol1:
            if st.button("Previous Set", key="prev_set"):
                app.set_index = (
                    app.num_train_sets - 1
                    if app.set_index == 0
                    else app.set_index - 1
                )
                app.current_set = app.current_annotation_sets[app.set_index]
                st.rerun()

            if st.button("✅ Confirm"):
                st.session_state.show_confirm_dialog = True
        with ccol2:

            if st.button("Next Set", key="next_set"):
                app.set_index = (app.set_index + 1) % app.num_train_sets
                app.current_set = app.current_annotation_sets[app.set_index]
                st.rerun()

            if st.button("Return"):
                if can_transition(app.page, Page.GREETING):
                    app.page = Page.GREETING
                    st.rerun()

        if st.session_state.get("show_confirm_dialog", False):
            confirm_dialog()

        if st.session_state.get("confirmed", False):
            if mode == AnnotateMode.ANNOTATE:
                if can_transition(app.page, Page.GREETING):
                    app.update_scan_metadata(app.current_annotation_sets)
                    app.page = Page.GREETING
                    st.session_state.confirmed = False  # reset
                    st.rerun()
            elif mode == AnnotateMode.VERIFY:
                if can_transition(app.page, Page.TESTING):
                    app.update_scan_metadata(app.current_annotation_sets)
                    app.page = Page.TESTING
                    st.session_state.confirmed = False
                    st.rerun()
