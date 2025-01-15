"""
Reusable UI components for the Streamlit application.
"""

import streamlit as st

def sidebar_content():
    """
    Create and display sidebar navigation content.
    
    Returns:
        str: Selected app mode
    """
    with st.sidebar:
        st.title("Navigation 🧭")
        
        # Add market research to options
        app_mode = st.radio(
            "Choose the app",
            ["Research Summarizer", "Problem Framing", "Market Research"]
        )
        
        st.markdown("---")
        st.header("Settings")
        if st.button("Clear Conversation"):
            st.session_state.memory.clear()
            st.session_state.chat_history = []
            st.experimental_rerun()
            
        return app_mode 