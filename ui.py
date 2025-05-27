import os
from typing import Tuple, Optional, Dict, List
import streamlit as st
from PIL import Image
import pandas as pd


from utils.dialog import confirm_dialog
from set_chooser import SetChooser
from app_state import AppState
from utils.credential_manager import CredentialManager
from utils.settings_loader import load_toml_config

CONFIG_PATH = "config.toml"
USER_PATH = "users.toml"

def init_state(config_path: str = "config.toml", user_path: str = "users.toml") -> Tuple[AppState, Optional[CredentialManager]]:
    st.set_page_config(
        page_title = "MedFabric - Collaborative Intelligence",
        page_icon = "🧠",
        layout = "wide",
        initial_sidebar_state = "expanded",
    )
    if "app" not in st.session_state:
        st.session_state.app = AppState(config=load_toml_config(config_path))
    if "cm" not in st.session_state:
        st.session_state.cm = _cm = CredentialManager(toml_file=user_path)
    _app = st.session_state.app
    _cm = st.session_state.cm
    return _app, _cm

app, cm = init_state()
if app.page == "greeting":
    app.set_greeting()
    st.title("Welcome to MedFabric - Collaborative Intelligence")
    username_input = st.text_input("Username:")
    password_input = st.text_input("Password:", type="password")
    if st.button("Login"):
        if not username_input or not password_input:
            st.error("Please enter both username and password.")
        else:
            if cm.verify_user(username_input, password_input):
                app.doctor_id = cm.get_user_id(username_input)
                st.success(f"Welcome back, {username_input}!")
                print(f"Doctor ID: {app.doctor_id}")
                app.logon = True
                app.page = "config"
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")

    if st.button("Register", key="register_redirect"):
        app.page = "registration"
        print(app.page)
        st.rerun()

elif app.page == "registration":
    st.title("Register a New User")
    username_input = st.text_input("Username:")
    password_input_1 = st.text_input("Password:", type="password")
    password_input_2 = st.text_input("Confirm Password:", type="password")

    if st.button("Register", key="register_button"):
        # Validate input
        if not username_input or not password_input_1 or not password_input_2:
            st.error("Please fill out all fields.")
        elif password_input_1 != password_input_2:
            st.error("Passwords do not match.")
        else:
            # Try adding user
            success = cm.add_user(username_input, password_input_1)
            if success:
                st.success(f"User '{username_input}' registered successfully!")
                # Set app state to redirect to login next run
                app.page = "greeting"
                st.rerun()
            else:
                st.error(f"User '{username_input}' already exists.")
elif app.page == "config":
    st.title("Configuration")
    num_train_sets = st.number_input("Number of Training Sets", min_value=1, max_value=10, value=5)
    num_test_sets = st.number_input("Number of Test Sets", min_value=1, max_value=10, value=5)
    if st.button("Save Configuration"):
        app.num_train_sets = num_train_sets
        app.num_test_sets = num_test_sets
        st.success("Configuration saved successfully!")
        app.page = "training"
        st.rerun()

elif app.page == "training":
    app.set_training_init()
    st.title("Training Phase")
    if st.button("Return"):
        app.page = "greeting"
        st.rerun()
    num_images = len(app.current_set.image_list)
    print(app.current_set.image_list)
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
        st.write(f"Current Set: {app.set_index + 1} of {app.num_train_sets}")
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
        st.table(df)

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
                    app.num_train_sets - 1
                    if app.set_index == 0
                    else app.set_index - 1
                )
                app.current_set = app.current_training_sets[app.set_index]
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
                app.set_index = (app.set_index + 1) % app.num_train_sets
                app.current_set = app.current_training_sets[app.set_index]
                st.rerun()

        if st.button("✅ Confirm"):
            confirm_dialog()