"""
Chat interface component for handling user interactions.
"""

import streamlit as st
from typing import List, Tuple

class ChatInterface:
    """Handles chat interface display and interactions."""
    
    @staticmethod
    def show_input_guidelines():
        """Display guidelines for user input."""
        with st.expander("ℹ️ Input Guidelines", expanded=False):
            st.markdown("""
            ### How to get the best results:
            1. **Be Specific**: Ask clear, focused questions
            2. **Context Matters**: Reference specific parts of the documents when relevant
            3. **Follow-up**: You can ask follow-up questions about previous answers
            
            ### Example Questions:
            - "What are the main challenges mentioned in the interviews?"
            - "Summarize the key findings about user needs"
            - "What solutions were proposed for [specific problem]?"
            """)

    @staticmethod
    def get_user_input() -> str:
        """
        Get user input from the chat interface.
        
        Returns:
            str: User's input question
        """
        return st.chat_input("Ask a question about the documents...")

    @staticmethod
    def display_chat_history(chat_history: List[Tuple[str, str]]):
        """
        Display the chat history.
        
        Args:
            chat_history: List of (question, answer) tuples
        """
        for i, (question, answer) in enumerate(chat_history):
            # User message
            message = st.chat_message("user")
            message.write(question)
            
            # Assistant message
            message = st.chat_message("assistant")
            message.write(answer) 