# app.py
import os
import streamlit as st
from PIL import Image

from AppChooser import AppState, SetChooser


def init_state():
    st.set_page_config(
    page_title="MedFabric - Collaborative Intelligence",
    page_icon="🩻",
    layout="wide",
    initial_sidebar_state="expanded",
)
    if "app" not in st.session_state:
        st.session_state.app = AppState()


# === BEGIN STREAMLIT APP ===
init_state()
app = st.session_state.app

# === PAGE LOGIC ===
if app.page == "greeting":
    st.title("Welcome to MedFabric - Collaborative Intelligence")
    app.id = st.text_input("Enter your ID:")
    if app.id == "1":
        if st.button("Configure"):
            app.page = "config"
            st.rerun()
    elif app.id != "":
        st.error("Invalid ID. Please enter a valid ID.")

elif app.page == "config":
    st.title("Configuration Page")
    num_sets = 0
    num_sets = st.number_input(
        "Number of sets to view:", min_value=5, max_value=15, value=5, step=1
    )
    if st.button("Confirm"):
        app.page = "training"
        app.set_chooser = SetChooser(app.id)
        app.set_chooser.initialize(num_sets)
        app.set_list = app.set_chooser.choose_set()
        app.current_set = app.set_list[0]
        app.set_index = 0
        st.rerun()

elif app.page == "training":
    st.title("Training Phase")
    if st.button("Return"):
        app.page = "greeting"
        st.rerun()
    if app.current_set.image_list:
        # Row: Buttons for doctor flags
        num_images = len(app.current_set.image_list)
        img_path = os.path.join(
            app.current_set.folder,
            app.current_set.image_list[app.current_set.image_index],
        )
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
            st.write(f"Current Set: {app.set_index + 1} of {len(app.set_list)}")
            st.write(f"Patient ID: {app.current_set.patient_id}")
            st.write(f"Scan Type: {app.current_set.scan_type}")
            st.write(f"Number of Images: {num_images}")
            st.write(f"Showing image {app.current_set.image_index+1} of {num_images}")
            for key, value in app.current_set.patient_metadata.items():
                if value != 0 and key != "patient_id" and key != "category":
                    st.write(f"{key}: {value}")
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
                if temp_quality_button and app.current_set.quality == 0:
                    app.current_set.quality = 1
                elif temp_quality_button and app.current_set.quality == 1:
                    app.current_set.quality = 0
                if app.current_set.quality == 1:
                    st.warning(
                        "Marked as Low Quality"
                    )  # Replace with your backend logic

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
                        len(app.set_list) - 1
                        if app.set_index == 0
                        else app.set_index - 1
                    )
                    app.current_set = app.set_list[app.set_index]
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
                    app.set_index = (app.set_index + 1) % len(app.set_list)
                    app.current_set = app.set_list[app.set_index]
                    st.rerun()

            if st.button("✅ Confirm"):
                st.success("Confirmed!")
                app.set_chooser.submit_to_df()
                app.page = "Testing"
                app.set_list = app.set_chooser.choose_set(mode="testing")
                app.current_set = app.set_list[0]
                app.set_index = 0
                st.rerun()

elif app.page == "Testing":
    st.title("Testing Phase")
    if st.button("Return"):
        app.page = "greeting"
        st.rerun()
    if app.current_set.image_list:
        # Row: Buttons for doctor flags
        num_images = len(app.current_set.image_list)
        img_path = os.path.join(
            app.current_set.folder,
            app.current_set.image_list[app.current_set.image_index],
        )
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
            st.write(f"Current Set: {app.set_index + 1} of {len(app.set_list)}")
            st.write(f"Number of Images: {num_images}")
            st.write(f"Showing image {app.current_set.image_index+1} of {num_images}")
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
                if temp_quality_button and app.current_set.quality == 0:
                    app.current_set.quality = 1
                elif temp_quality_button and app.current_set.quality == 1:
                    app.current_set.quality = 0
                if app.current_set.quality == 1:
                    st.warning(
                        "Marked as Low Quality"
                    )  # Replace with your backend logic

            # Row: Number inputs for regions
            st.markdown("### Therapeutic Markings")
            ccol1, ccol2 = st.columns([1, 1])
            with ccol1:
                basel = st.number_input(
                    "Basel Ganglia Image:",
                    min_value=1,
                    max_value=num_images,
                    value=app.current_set.opinion_basel + 1,
                )
                app.current_set.opinion_basel = basel - 1
                if st.button("Previous Set", key="prev_set"):
                    app.set_index = (
                        len(app.set_list) - 1
                        if app.set_index == 0
                        else app.set_index - 1
                    )
                    app.current_set = app.set_list[app.set_index]
                    st.rerun()

            with ccol2:
                thalamus = st.number_input(
                    "Thalamus Image:",
                    min_value=1,
                    max_value=num_images,
                    value=app.current_set.opinion_thalamus + 1,
                )
                app.current_set.opinion_thalamus = thalamus - 1

                if st.button("Next Set", key="next_set"):
                    app.set_index = (app.set_index + 1) % len(app.set_list)
                    app.current_set = app.set_list[app.set_index]
                    st.rerun()

            if st.button("✅ Confirm"):
                st.success("Confirmed!")
                app.page = "greeting"
                st.rerun()
