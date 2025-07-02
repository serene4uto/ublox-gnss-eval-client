import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Logs Analysis",
    page_icon="📊",
    layout="wide"
)

st.title("Logs Analysis")

# File uploader widget
first_log_file = st.file_uploader(
    "Upload the 1st gnss log file (CSV)",
    type=["csv"],
    key="first_log_file_uploader"
)

second_log_file = st.file_uploader(
    "Upload the 2nd gnss log file (CSV)",
    type=["csv"],
    key="second_log_file_uploader"
)

# Function to read and process the CSV files