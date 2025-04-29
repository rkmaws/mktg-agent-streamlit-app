import streamlit as st
from src.ui import demo_ui
import logging
logger = logging.getLogger(__name__)

def content_section():
    st.header("AWS Agentic AI Demo powered by Amazon Bedrock Agents", divider="rainbow")
    demo_ui.main()

if __name__ == "__main__":
    content_section()