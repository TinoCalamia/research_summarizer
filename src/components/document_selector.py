"""
Document selector component for handling document selection in the UI.
"""

import streamlit as st
from typing import List, Set

class DocumentSelector:
    """Handles document selection interface and logic."""
    
    @staticmethod
    def show_selector(document_names: List[str]) -> Set[str]:
        """
        Display document selection interface with all documents pre-selected.
        
        Args:
            document_names: List of available document names
            
        Returns:
            Set[str]: Selected document names
        """
        st.sidebar.markdown("## Loaded Documents")
        st.sidebar.markdown("Uncheck to exclude documents from analysis:")
        
        # Initialize selection state if not exists or if document list changed
        if ('document_selection' not in st.session_state or 
            len(st.session_state.document_selection) != len(document_names)):
            st.session_state.document_selection = set(document_names)
        
        # Individual document selection
        selected = set()
        for doc in document_names:
            # Default to True for pre-selecting
            if st.sidebar.checkbox(
                doc,
                value=True,  # Always default to True
                key=f"doc_{doc}"
            ):
                selected.add(doc)
        
        # Update stored selection
        st.session_state.document_selection = selected
        
        return selected

    @staticmethod
    def get_initial_selection(document_names: List[str]) -> Set[str]:
        """
        Get the initial selection state (all documents selected).
        
        Args:
            document_names: List of available document names
            
        Returns:
            Set[str]: All document names as a set
        """
        return set(document_names) 