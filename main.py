"""MedFabric System
Main entry point for the MedFabric Streamlit application."""
from init import init_state, render, CONFIG_PATH, USER_PATH
from app_state import Page

app_, cm_ = init_state(CONFIG_PATH, USER_PATH)
render(app_, cm_, Page.TRAINING)
