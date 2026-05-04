# app/styles.py
# Injects custom CSS into Streamlit for better UI polish.
# Call inject_styles() at the top of any Streamlit page.

import streamlit as st


def inject_styles():
    st.markdown("""
    <style>
    /* Chat message styling */
    .stChatMessage {
        border-radius: 12px;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
    }

    /* Source expander styling */
    .streamlit-expanderHeader {
        font-size: 0.85rem;
        color: #1B4F72;
    }

    /* Sample question buttons */
    .stButton button {
        text-align: left;
        height: auto;
        white-space: normal;
        border-radius: 8px;
        border: 1px solid #D5D8DC;
        background-color: #EBF5FB;
        color: #1C2833;
        font-size: 0.88rem;
        padding: 0.6rem 0.8rem;
    }
    .stButton button:hover {
        border-color: #1B4F72;
        background-color: #D6EAF8;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #1B4F72;
    }
    </style>
    """, unsafe_allow_html=True)
