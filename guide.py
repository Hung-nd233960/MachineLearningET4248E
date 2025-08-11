import streamlit as st
from pathlib import Path
import re

file_path = Path("docs/UserGuide.md").read_text(encoding="utf-8")

st.markdown(file_path, unsafe_allow_html=True)
