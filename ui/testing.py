import os
from PIL import Image

import pandas as pd
import streamlit as st
from app_state import AppState, Page, can_transition

def testing(app: AppState) -> None:
    """Display the testing phase screen."""
    if app.testing_initialized is False:
        app.update_scan_metadata(app.current_annotation_sets)
        app.init_trainer()
        app.train_model()
        app.set_test_init()
        app.current_set = app.current_testing_sets[app.set_index]
        app.test_model()
    st.title("Testing Phase")
    if st.button("Return"):
        if can_transition(app.page, Page.GREETING):
            app.page = Page.GREETING
            st.rerun()
    num_images = len(app.current_set.image_list)
    img_path = os.path.join(app.current_set.folder,
                            app.current_set.image_list[app.current_set.image_index])
    column1, column2, column3 = st.columns([1, 1, 1])
    with column1:
        img = Image.open(img_path)
        st.image(img)
        col1, col2 = st.columns([6, 2])
        with col1:
            if st.button("⬅️ Previous", key="prev_img"):
                app.current_set.image_index = (
                    app.current_set.image_index - 1
                ) % num_images
                st.rerun()

        with col2:
            if st.button("Next ➡️", key="next_img"):
                app.current_set.image_index = (
                    app.current_set.image_index + 1
                ) % num_images
                st.rerun()

        slider_val = st.slider(
            "Jump to image", 1, num_images, app.current_set.image_index + 1
        )
        if slider_val - 1 != app.current_set.image_index:
            app.current_set.image_index = slider_val - 1
            st.rerun()

    with column2:
        st.write(f"Current Set: {app.set_index + 1} of {app.num_test_sets}")
        st.write(f"Patient ID: {app.current_set.patient_id}")
        st.write(f"Scan Type: {app.current_set.scan_type}")
        st.write(f"Showing image {app.current_set.image_index+1} of {num_images}")

        # Filter out unwanted keys
        metadata = {
            key: value
            for key, value in app.current_set.patient_metadata.items()
            if key != "patient_id" and key != "Category"
        }

        diagnoses = {}

        for key, value in metadata.items():
            if ":" in key:
                rater, diagnosis = key.split(":", 1)
                diagnoses.setdefault(diagnosis, {})[rater] = value

        # Create DataFrame
        df = pd.DataFrame.from_dict(diagnoses, orient='index').fillna(0).astype(int)

        # Optional: sort columns and index for nicer display
        df = df.sort_index().sort_index(axis=1)

        # Display the table
        st.markdown("### Patient Metadata")
        st.dataframe(df, use_container_width=True)

    with column3:
        st.markdown("### Doctor's Technical Evaluation")
        bcol1, bcol2 = st.columns([1, 1])
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
        
        # Row: Number inputs for regions
        st.markdown("### Therapeutic Markings")
        ccol1, ccol2 = st.columns([1, 1])
        with ccol1:
            basel = st.number_input(
                "Basel Ganglia Image:",
                min_value=1,
                max_value=num_images,
                value=app.current_set.opinion_basel,
            )
            app.current_set.opinion_basel = basel

            if st.button("Previous Set", key="prev_set"):
                app.set_index = (
                    app.num_test_sets - 1
                    if app.set_index == 0
                    else app.set_index - 1
                )
                app.current_set = app.current_testing_sets[app.set_index]
                st.rerun()
        with ccol2:
            thalamus = st.number_input(
                "Thalamus Image:",
                min_value=1,
                max_value=num_images,
                value=app.current_set.opinion_thalamus,
            )
            app.current_set.opinion_thalamus = thalamus

            if st.button("Next Set", key="next_set"):
                app.set_index = (app.set_index + 1) % app.num_test_sets
                app.current_set = app.current_testing_sets[app.set_index]
                st.rerun()

        if st.button("✅ Confirm"):
            app.update_scan_metadata(app.current_testing_sets)
            st.success("Data updated successfully!")
            if can_transition(app.page, Page.GREETING):
                app.page = Page.GREETING
                st.rerun()