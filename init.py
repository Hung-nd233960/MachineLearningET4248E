from typing import Tuple, Optional
import streamlit as st
from app_state import AppState, Page

from utils.credential_manager import CredentialManager
from utils.settings_loader import load_toml_config

from ui.greetings import greeting
from ui.registration import registration
from ui.configuration import configuration
from ui.annotation import annotation_screen
from ui.testing import testing

CONFIG_PATH = "config.toml"
USER_PATH = "users.toml"

def init_state(config_path: str = "config.toml", 
               user_path: str = "users.toml") -> Tuple[AppState, CredentialManager]:
    """Initialize the Streamlit app state and credential manager."""
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


def render(app: AppState, cm: CredentialManager, destination: Optional[Page] =  None) -> None:
    """Render the appropriate page based on the app state."""
    if destination is None:
        target_page = app.page
    else:
        target_page = destination
    
    if target_page == Page.GREETING and not app.logon:
            greeting(app, cm)
    elif target_page == Page.REGISTRATION:
        registration(app, cm)
    elif target_page == Page.CONFIGURATION:
        configuration(app)
    elif target_page == Page.TRAINING:
        app.set_annotation_init()
        annotation_screen(app)
    elif target_page == Page.TESTING:
        testing(app)
    else:
        st.error("Unknown page state.")