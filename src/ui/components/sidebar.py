"""
Sidebar component for the main application.
"""

import streamlit as st

def sidebar_content() -> str:
    """
    Display and handle sidebar content.
    
    Returns:
        str: Selected application mode
    """
    with st.sidebar:
        st.title("Research Assistant")
        
        # App mode selection
        app_mode = st.radio(
            "Choose Analysis Mode",
            ["Solution Explorer", "Research Summarizer", "Problem Framing", "Market Research", ],
            index=0  # Default to Research Summarizer
        )
        
        st.markdown("---")
        
    return app_mode 