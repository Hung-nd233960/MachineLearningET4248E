from typing import Tuple, Optional
import streamlit as st
from app_state import AppState, Page

from utils.credential_manager import CredentialManager
from utils.settings_loader import load_toml_config

from ui.greetings import greeting
from ui.registration import registration
from ui.configuration import configuration
from ui.annotation import annotation_screen, AnnotateMode
from ui.testing import testing
from ui.dashboard import dashboard

CONFIG_PATH = "config.toml"
USER_PATH = "users.toml"


def init_state(
    config_path: str = "config.toml", user_path: str = "users.toml"
) -> Tuple[AppState, CredentialManager]:
    """Initialize the Streamlit app state and credential manager."""
    st.set_page_config(
        page_title="MedFabric - Collaborative Intelligence",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    if "app" not in st.session_state:
        st.session_state.app = AppState(config=load_toml_config(config_path))
    if "cm" not in st.session_state:
        st.session_state.cm = _cm = CredentialManager(toml_file=user_path)
    _app = st.session_state.app
    _app.set_credential_manager(st.session_state.cm)
    _cm = st.session_state.cm
    return _app, _cm


def render(
    app: AppState, cm: CredentialManager, destination: Optional[Page] = None
) -> None:
    """Render the appropriate page based on the app state."""
    if destination is None:
        target_page = app.page
    else:
        target_page = destination

    if target_page == Page.GREETING:
        greeting(app, cm)
    elif target_page == Page.REGISTRATION:
        registration(app, cm)
    elif target_page == Page.DASHBOARD:
        dashboard(app)
    elif target_page == Page.CONFIGURATION:
        configuration(app, cm)
    elif target_page == Page.ANNOTATION:
        if app.doctor_role == "verifier":
            app.set_verification_init()
            annotation_screen(app, AnnotateMode.VERIFY)
        elif app.doctor_role == "labeler":
            app.set_annotation_init()
            annotation_screen(app, AnnotateMode.ANNOTATE)
    elif target_page == Page.TESTING:
        testing(app)
    else:
        st.error("Unknown page state.")
