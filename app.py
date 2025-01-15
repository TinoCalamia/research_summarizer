"""
Main application entry point for the Research Assistant tool.
"""

import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Add the project root to Python path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import UI components and pages
from src.ui.components.sidebar import sidebar_content
from src.ui.pages.market_research import show_market_research
from src.ui.pages.problem_framing import show_problem_framing
from src.ui.pages.research_summarizer import show_summarizer
from src.ui.pages.solution_explorer import show_solution_explorer

# Import utilities
from src.utils.loader import load_folder_docs
from src.utils.memory import create_summary_memory

def init_session_state():
    """Initialize session state variables."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'llm' not in st.session_state:
        st.session_state.llm = ChatOpenAI(
            temperature=0,
            model="gpt-4-1106-preview"
        )
    
    if 'all_documents' not in st.session_state:
        st.session_state.all_documents = load_folder_docs()
        st.session_state.document_names = [
            doc.metadata.get('source', '').split('/')[-1] 
            for doc in st.session_state.all_documents
        ]

def main():
    """Main application entry point."""
    # Load environment variables
    load_dotenv()
    
    # Initialize session state
    init_session_state()
    
    # Get selected mode from sidebar
    app_mode = sidebar_content()
    
    # Display selected page
    if app_mode == "Research Summarizer":
        show_summarizer()
    elif app_mode == "Problem Framing":
        show_problem_framing()
    elif app_mode == "Market Research":
        show_market_research()
    elif app_mode == "Solution Explorer":
        show_solution_explorer()

if __name__ == "__main__":
    main()
